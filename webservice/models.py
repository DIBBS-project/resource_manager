from django.db import models
import uuid


def generate_uuid():
    return "%s" % (uuid.uuid4())


class Token(models.Model):
    token = models.CharField(max_length=100, blank=False, default=generate_uuid)
    user_id = models.IntegerField()
    username = models.TextField(blank=True, default="root")


class Job(models.Model):
    name = models.CharField(max_length=100, blank=False, default=generate_uuid)
    status = models.CharField(max_length=100, blank=False, default="created")
    command = models.TextField(blank=True, default="")
    callback_url = models.TextField(blank=True, default="")
    user = models.CharField(max_length=100, blank=False, default="cc")


class Execution(models.Model):
    application_hadoop_id = models.CharField(max_length=100, blank=False, default=generate_uuid, unique=True)
    job = models.ForeignKey(Job, to_field='id')
