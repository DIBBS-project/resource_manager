# coding: utf-8
from __future__ import absolute_import, print_function

import uuid

from django.conf import settings
from django.contrib import auth
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from jsonfield import JSONField
from rest_framework.authtoken.models import Token

from rmapp import crypto
from rmapp import remote


class Credential(models.Model):
    """
    Credentials that DIBBs users have with cloud (OpenStack) service
    providers. Stored with reversable RSA-OAEP encryption as we must be
    able to pull out the plaintext credentials to interact with the cloud
    service.

    RSA keys stored in the Profile model/table.
    """
    site_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='credentials', on_delete=models.CASCADE)
    credentials = models.TextField()


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True,
                                related_name='profile')
    rsa_private = models.TextField(max_length=1024, default=crypto.generate_rsa_key)

    @property
    def rsa_public(self):
        return crypto.private_to_public(self.rsa_private)


class Cluster(models.Model):
    name = models.CharField(max_length=100, blank=True, default='')
    uuid = models.CharField(max_length=100, blank=False, default=uuid.uuid4)
    private_key = models.TextField(max_length=1000, blank=True, default='')
    public_key = models.TextField(max_length=1000, blank=True, default='')

    status = models.CharField(max_length=100, blank=True, default='IDLE')
    hints = models.CharField(max_length=100, blank=True, default='{}')
    credential = models.CharField(max_length=100, blank=True, default='')

    targeted_slaves_count = models.IntegerField(default=0)
    current_slaves_count = models.IntegerField(default=0)

    # Relationships
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='clusters', on_delete=models.PROTECT)
    appliance = models.CharField(max_length=100)
    appliance_impl = models.CharField(max_length=100, blank=True)
    common_appliance_impl = models.CharField(max_length=100, blank=True)

    @property
    def master_node(self):
        return Host.objects.get(cluster_id=self.id, is_master=True)

    @property
    def service_url(self):
        master_node_ip = self.master_node.instance_ip
        return 'http://{}:{}'.format(master_node_ip, 8012)

    def get_full_credentials(self):
        appl_impl = remote.appliance_impl_name_get(str(self.appliance_impl))

        cred_filter = {
            'site_name': appl_impl.site,
        }
        if self.credential == '':
            cred_filter['user'] = self.user
        else:
            cred_filter['name'] = self.credential

        credential = Credential.objects.filter(**cred_filter).first()
        profile = Profile.objects.get(user=self.user)

        return {
            "site": remote.sites_name_get(credential.site_name),
            "user": self.user,
            "credentials": crypto.decrypt_credentials(credential.credentials, profile.rsa_private),
        }


class Host(models.Model):
    name = models.CharField(max_length=100, blank=True, default='')
    is_master = models.BooleanField(default=False)
    instance_id = models.CharField(max_length=100, blank=True, default='')
    instance_ip = models.CharField(max_length=100, blank=True, default='')

    # Relationships
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)


class ClusterCredential(models.Model):
    """
    Credentials that DIBBs users have on deployed clusters. Allows re-use of
    the accounts for DIBBs Operations rather than creating a new user per-Op.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100, blank=True)
