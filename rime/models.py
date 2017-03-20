import base64
import json
import logging
import uuid

from django.conf import settings
from django.db import models
import heatclient.exc as heat_exc
import yaml

from . import openstack
from . import remote
from . import tasks


logger = logging.getLogger(__name__)


def deobfuscate(serialized_data):
    return json.loads(base64.b64decode(serialized_data.encode('utf-8')).decode('utf-8'))


def lazyprop(fn):
    attr_name = '_lazy_' + fn.__name__
    @property
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazyprop


class Cluster(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # name = models.CharField(max_length=100, blank=True, default='')
    # private_key = models.TextField(max_length=1000, blank=True, default='')
    # public_key = models.TextField(max_length=1000, blank=True, default='')

    # status = models.CharField(max_length=100, blank=True, default='IDLE')
    # hints = models.CharField(max_length=100, blank=True, default='{}')
    root_owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='clusters', on_delete=models.PROTECT)
    credential = models.ForeignKey('Credential', on_delete=models.PROTECT)

    appliance = models.CharField(max_length=2048)
    site = models.CharField(max_length=2048)
    implementation = models.CharField(max_length=2048)

    remote_id = models.CharField(max_length=2048)
    remote_status = models.CharField(max_length=200, default='UNCREATED')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def delete(self):
        try:
            self.heat_client.stacks.delete(self.remote_id)
        except heat_exc.HTTPNotFound as e:
            logger.info('Stack {}: Remote stack {} already gone (404 from service)'.format(self.id, self.remote_id))
        super().delete()

    @lazyprop
    def keystone_session(self):
        # if self._keystone_session is None:
        creds = self.credential.deobfuscated_credentials
        creds['auth_url'] = self.site_data['api_url']
        return openstack.keystone_session(creds)
        # return self._keystone_session

    @lazyprop
    def heat_client(self):
        return openstack.heat_client(session=self.keystone_session)

    @lazyprop
    def nova_client(self):
        return openstack.nova_client(session=self.keystone_session)

    @lazyprop
    def site_data(self):
        return remote.site(self.site)

    @lazyprop
    def implementation_data(self):
        return remote.implementation(self.implementation)

    @lazyprop
    def template(self):
        template = self.implementation_data['script']
        template = yaml.safe_load(template)
        # the heat client doesn't like dates, which PyYAML helpfully deserialized for us...
        template['heat_template_version'] = template['heat_template_version'].strftime('%Y-%m-%d')
        return template

    def get_stack(self):
        return self.heat_client.stacks.get(self.remote_id)

    def monitor_transition(self):
        logger.info('Beginning remote state monitoring')
        return tasks.monitor_cluster.delay(self.id)


class Credential(models.Model):
    """
    Credentials that DIBBs users have with cloud (e.g. OpenStack) service
    providers. Stored HACK in plaintext TODO with reversable encryption as we must be
    able to pull out the plaintext credentials to interact with the cloud
    service.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    site = models.CharField(max_length=2048)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='credentials', on_delete=models.CASCADE)
    credentials = models.TextField()

    @property
    def deobfuscated_credentials(self):
        """Reverse the base64-encoded JSON."""
        return deobfuscate(self.credentials)


class Resource(models.Model):
    """
    High-level "Resource" abstraction on top of real computing resources that
    DIBBs users have on deployed clusters. Creates accounts for a cluster
    on-first-use that can be reused for other DIBBs Operations rather than
    creating a new user per-Op.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cluster = models.ForeignKey('Cluster', on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100, blank=True)
