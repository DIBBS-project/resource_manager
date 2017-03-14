# from django.contrib.auth import get_user_model
import requests
from rest_framework import serializers

from . import models, remote


class CredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Credential
        fields = ('id', 'name', 'site', 'user', 'created')
        read_only_fields = ('id', 'user')
        # extra_kwargs = {
        #     'password': {'write_only': True}
        # }

    def validate_site(self, name):
        try:
            site_data = remote.site(name)
        except requests.HTTPError as e:
            raise serializers.ValidationError("Site not found")
        return name


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Resource
        fields = ('id', 'root_owner', 'credential', 'site', 'appliance', 'implementation')
        read_only_fields = fields
        # extra_kwargs = {
        #     'password': {'write_only': True}
        # }

    # credential = serializers.HyperlinkedRelatedField(
    credential = serializers.PrimaryKeyRelatedField(
    #     view_name='credential-detail',
        queryset=models.Credential.objects.all(),
    )
    root_owner = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault(),
    )

    # def validate_site(self, name):
    #     try:
    #         site_data = remote.site(name)
    #     except requests.HTTPError as e:
    #         raise serializers.ValidationError("Site not found")
    #     return name
