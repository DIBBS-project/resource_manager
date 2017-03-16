import uuid

from django.conf import settings
from django.db import models


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
