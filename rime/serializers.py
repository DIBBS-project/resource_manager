import base64
import json

# from django.contrib.auth import get_user_model
import requests
from rest_framework import serializers

from . import models, remote
from .models import deobfuscate


# class CredentialSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Credential
#         fields = ('id', 'name', 'site', 'user', 'created', 'credentials')
#         read_only_fields = ('id', 'user')
#         extra_kwargs = {
#             'credentials': {'write_only': True}
#         }
#
#     def validate_site(self, name):
#         try:
#             site_data = remote.site(name)
#         except requests.HTTPError as e:
#             raise serializers.ValidationError("Site not found")
#         return name
#
#     def validate_credentials(self, value):
#         try:
#             cred_data = deobfuscate(value)
#         except (json.decoder.JSONDecodeError, UnicodeDecodeError):
#             raise serializers.ValidationError("Invalid base64-encoded JSON")
#
#         missing_fields = {'username', 'password', 'project_name'} - set(cred_data)
#         if missing_fields:
#             raise serializers.ValidationError('Missing fields: {}'.format(missing_fields))
#
#         return value


class ClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cluster
        fields = (
            'id', 'root_owner', 'credential', 'implementation', 'remote_id',
            'remote_status', 'status', 'address',
        )
        read_only_fields = (
            'id', 'root_owner', 'remote_id', 'remote_status', 'status',
            'address',
        )
        # extra_kwargs = {
        #     'password': {'write_only': True}
        # }

    credential = serializers.PrimaryKeyRelatedField(
        queryset=models.Credential.objects.all(),
    )
    # root_owner = serializers.PrimaryKeyRelatedField(
    #     read_only=True,
    #     default=serializers.CurrentUserDefault(),
    # )

    def validate_implementation(self, name):
        try:
            self.imp_data = remote.implementation(name)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise serializers.ValidationError("Implementation not found")
            else:
                raise
        return name

    def validate(self, data):
        data['appliance'] = self.imp_data['appliance']
        data['site'] = self.imp_data['site']
        if data['credential'].site != data['site']:
            raise serializers.ValidationError("Credential site doesn't match Implementation site")
        return data


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Resource
        fields = ('id', 'user', 'cluster', 'hints', 'username', 'password')
        read_only_fields = ('id', 'user', 'cluster', 'hints', 'username', 'password')
