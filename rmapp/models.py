# coding: utf-8
from __future__ import absolute_import, print_function

import uuid

from Crypto.PublicKey import RSA
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from rmapp import crypto
from rmapp import remote


RSA_KEY_LENGTH = 2048


class Credential(models.Model):
    site_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='credentials', on_delete=models.CASCADE)
    credentials = models.TextField()


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True,
                                related_name='profile')
    rsa_key = models.TextField(max_length=1024, blank=True, default='')


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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='clusters', on_delete=models.CASCADE)
    appliance = models.CharField(max_length=100)
    appliance_impl = models.CharField(max_length=100, blank=True)
    common_appliance_impl = models.CharField(max_length=100, blank=True)

    @property
    def master_node(self):
        return Host.objects.get(cluster_id=self.id, is_master=True)

    def get_full_credentials(self):
        appl_impl = remote.appliance_impl_name_get(str(self.appliance_impl))

        user = auth.get_user_model().objects.get(id=self.user_id)
        full_credentials = None
        possible_credentials = user.credentials.all() if self.credential == "" else Credential.objects.filter(name=self.credential)
        for creds in possible_credentials:
            if creds.site_name == appl_impl.site:
                profile = Profile.objects.get(user_id=self.user_id)
                full_credentials = {
                    "site": remote.sites_name_get(creds.site_name),
                    "user": self.user,
                    "credentials": crypto.decrypt_credentials(creds.credentials, profile),
                }
                break
        return full_credentials


class ClusterCredential(models.Model):
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    dibbs_user = models.CharField(max_length=100)
    resource_credentials = models.CharField(max_length=250, default='{}')


class Host(models.Model):
    name = models.CharField(max_length=100, blank=True, default='')
    is_master = models.BooleanField(default=False)
    instance_id = models.CharField(max_length=100, blank=True, default='')
    instance_ip = models.CharField(max_length=100, blank=True, default='')

    # Relationships
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)


# Add a token upon user creation
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


# Add a profile upon user creation
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance=None, created=False, **kwargs):
    if created:
        Profile.objects.create(user=instance, rsa_key=RSA.generate(RSA_KEY_LENGTH).exportKey())
