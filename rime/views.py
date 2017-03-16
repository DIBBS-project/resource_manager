import hashlib
import json
import logging

from django.conf import settings
from rest_framework import viewsets
import yaml

from . import models
from . import openstack
from . import remote
from . import serializers

# from .serializers import deobfuscate

logger = logging.getLogger(__name__)


class CredentialViewSet(viewsets.ModelViewSet):
    queryset = models.Credential.objects.all()
    serializer_class = serializers.CredentialSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClusterViewSet(viewsets.ModelViewSet):
    queryset = models.Cluster.objects.all()
    serializer_class = serializers.ClusterSerializer

    def perform_create(self, serializer):
        cluster = serializer.save(root_owner=self.request.user)
        imp = serializer.imp_data # volatile from validation...

        # get full connection information
        site = remote.site(imp['site'])
        # credential = models.Credential.objects.get(id=serializer.data['credential'])
        credential = cluster.credential
        credentials = credential.deobfuscated_credentials
        credentials['auth_url'] = site['api_url']
        session = openstack.keystone_session(credentials)

        # return
        # get template
        #imp = remote.implementation(serializer.data['implementation'])
        template = imp['script']
        logger.info('Using template, {} long, {} SHA256'.format(
            len(template),
            hashlib.sha256(template.encode('utf-8')).hexdigest(),
        ))
        template = yaml.safe_load(template)
        template['heat_template_version'] = template['heat_template_version'].strftime('%Y-%m-%d')

        # build template parameters
        heat_client = openstack.heat_client(session=session)
        nova_client = openstack.nova_client(session=session)
        parameters = {
            'cluster_size': 1,
            'image_name': 'CENTOS-7-HADOOP',
            'user_name': 'root',
            'flavor_name': openstack.get_flavor(nova_client),
            'network_name': openstack.get_network(nova_client),
            # "allowed_ips": public_ips,
            'allowed_ip': settings.PUBLIC_IP + '/32', # see above
        }
        logger.info('Stack parameters: {}'.format(json.dumps(parameters)))

        environment = {
            'parameters': parameters
        }
        stack = {
            'stack_name': 'LL-{}'.format(cluster.id),#cluster.name,
            'template': template,
            'environment': environment,
            'files': {},
            'parameters': {},
            'disable_rollback': True,
        }
        # print(json.dumps(stack, indent=4))
        print(stack)
        response = heat_client.stacks.create(**stack)
        logger.info('Response: {}'.format(json.dumps(response)))
        # stack_id = response["stack"]["id"] if "stack" in response and "id" in response["stack"] else None
        logger.info('Created stack {}'.format(response['stack']['id']))

        cluster.remote_id = response['stack']['id']
        cluster.save()


def get_or_create_resource(user, appliance: 'identifier', hints: dict = None):
    # find a cluster running the correct appliance
    # - also verify user has credentials on the site? soft privilege escalation hole
    # - validate those credentials? still poorly-controlled cross-talk between remote OS user privileges
    #   create/schedule resource creation (contact agent to generate credentials)

    # failing that, we need to create a cluster and put a resource on top of it

    # find an implementation that's the intersection of those that:
    # - implement the appliance (duh)
    # - were hinted (if provided)
    # - run on a site that the user has credentials to (limit sites and credentials if respectively hinted)
    if hints:
        if 'implementations' in hints:
            # fetch all implementation specs
            for imp_ref in hints['implementations']:
                imp = get_imp(imp_ref)
                ...

            # see if the
        if 'sites' in hints:
            pass

    else:
        pass
