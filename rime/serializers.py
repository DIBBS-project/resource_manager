# from django.contrib.auth import get_user_model
from rest_framework import serializers

from . import models


class CredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Credential
        fields = ('id', 'name', 'site', 'user', 'created')
        read_only_fields = ('id', 'user')
#         extra_kwargs = {
#             'password': {'write_only': True}
#         }
