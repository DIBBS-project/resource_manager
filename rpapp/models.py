from django.db import models
import uuid

# Create your models here.


def generate_uuid():
    return uuid.uuid4()


class User(models.Model):
    username = models.CharField(max_length=100, blank=False, default='')
    password = models.CharField(max_length=100, blank=False, default='')
    project = models.CharField(max_length=100, blank=False, default='')
    # Authentication
    api_token = models.TextField(max_length=1000, blank=True, default=str(uuid.uuid4()))
    security_certificate = models.TextField(max_length=1000, blank=True, default='')
    has_password = models.BooleanField(default=False)
    USERNAME_FIELD = 'identifier'


class Token(models.Model):
    value = models.TextField(max_length=1000, blank=True, default='')
    # Relationships
    user = models.ForeignKey("User", on_delete=models.CASCADE)


class Site(models.Model):
    name = models.CharField(max_length=100, blank=False, default='KVM@TACC')
    os_auth_url = models.CharField(max_length=1000, blank=False)


class Cluster(models.Model):
    name = models.CharField(max_length=100, blank=True, default='')
    uuid = models.CharField(max_length=100, blank=False, default=generate_uuid)
    private_key = models.TextField(max_length=1000, blank=True, default='')
    public_key = models.TextField(max_length=1000, blank=True, default='')

    # Relationships
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    site = models.ForeignKey("Site", on_delete=models.CASCADE)
    software = models.IntegerField()

    def get_master_node(self):
        candidates = Host.objects.filter(cluster_id=self.id).filter(is_master=True)
        return candidates[0] if len(candidates) > 0 else None

    def get_software_name(self):
        # TODO: fix hardcoded
        # FIXME
        # return self.software.name if self.software is not None else None
        return 'hadoop'

    # def user(self):


class Host(models.Model):
    name = models.CharField(max_length=100, blank=True, default='')
    is_master = models.BooleanField(default=False)
    instance_id = models.CharField(max_length=100, blank=True, default='')
    keypair = models.TextField(max_length=1000, blank=True, default='MySshKey')
    instance_ip = models.CharField(max_length=100, blank=True, default='')

    # Relationships
    cluster = models.ForeignKey("Cluster", on_delete=models.CASCADE)