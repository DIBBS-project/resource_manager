import uuid

from django.db import models


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
    # service_url
    #
    # def get_full_credentials(self):
    #     appl_impl = remote.appliance_impl_name_get(str(self.appliance_impl))
    #
    #     cred_filter = {
    #         'site_name': appl_impl.site,
    #     }
    #     if self.credential == '':
    #         cred_filter['user'] = self.user
    #     else:
    #         cred_filter['name'] = self.credential
    #
    #     credential = Credential.objects.filter(**cred_filter).first()
    #     profile = Profile.objects.get(user=self.user)
    #
    #     return {
    #         "site": remote.sites_name_get(credential.site_name),
    #         "user": self.user,
    #         "credentials": crypto.decrypt_credentials(credential.credentials, profile.rsa_private),
    #     }


class UserCluster(models.Model):
    """
    Credentials that DIBBs users have on deployed clusters. Allows re-use of
    the accounts for DIBBs Operations rather than creating a new user per-Op.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100, blank=True)
