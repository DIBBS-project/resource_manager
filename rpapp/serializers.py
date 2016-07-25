from rest_framework import serializers
from models import User, Cluster, Host


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField(max_length=100, allow_blank=False, default='')
    # password = serializers.CharField(max_length=100, allow_blank=False, default='')
    project = serializers.CharField(max_length=100, allow_blank=False, default='')
    api_token = serializers.CharField(max_length=100, allow_blank=False, default='')
    security_certificate = serializers.CharField(max_length=100, allow_blank=False, default='')

    cluster_ids = serializers.SerializerMethodField('user_clusters')

    def user_clusters(self, user):
        return map(lambda x: x.id, Cluster.objects.filter(user_id=user.id))

    def create(self, validated_data):
        """
        Create and return a new `User` instance, given the validated data.
        """
        return UserSerializer.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `User` instance, given the validated data.
        """
        instance.username = validated_data.get('username', instance.username)
        # instance.password = validated_data.get('password', instance.password)
        instance.project = validated_data.get('project', instance.project)

        if instance.password != "" and instance.password != "" and instance.project != "":
            instance.save()
        return instance


class ClusterSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=100, allow_blank=False, default='')
    uuid = serializers.CharField(max_length=100, allow_blank=True, default='')

    status = serializers.CharField(max_length=100, allow_blank=True, default='')

    # private_key = serializers.CharField(max_length=1000, allow_blank=True, default='')
    public_key = serializers.CharField(max_length=1000, allow_blank=True, default='')
    # has_password = serializers.BooleanField(default=False)
    appliance_impl = serializers.CharField(max_length=100, allow_blank=True, default='')
    common_appliance_impl = serializers.CharField(max_length=100, allow_blank=True, default='')

    # Relationships
    user_id = serializers.IntegerField()
    appliance = serializers.CharField(max_length=100)

    # Custom fields
    host_ids = serializers.SerializerMethodField('cluster_hosts')
    master_node_id = serializers.SerializerMethodField('cluster_master_node_id')
    master_node_ip = serializers.SerializerMethodField('cluster_master_node_ip')
    hosts_ips = serializers.SerializerMethodField('cluster_hosts_ips')

    def cluster_hosts(self, cluster):
        return map(lambda x: x.id, Host.objects.filter(cluster_id=cluster.id))

    def cluster_master_node_id(self, cluster):
        candidates = map(lambda x: x.id, Host.objects.filter(cluster_id=cluster.id).filter(is_master=True))
        return candidates[0] if len(candidates) > 0 else None

    def cluster_master_node_ip(self, cluster):
        candidates = map(lambda x: x.instance_ip, Host.objects.filter(cluster_id=cluster.id).filter(is_master=True))
        return candidates[0] if len(candidates) > 0 else None

    def cluster_hosts_ips(self, cluster):
        candidates = map(lambda x: x.instance_ip, Host.objects.filter(cluster_id=cluster.id))
        return candidates

    def cluster_appliance_name(self, cluster):
        return cluster.get_appliance_name()

    def create(self, validated_data):
        """
        Create and return a new `Cluster` instance, given the validated data.
        """
        return Cluster.objects.create(**validated_data)

    def update(self, instance, validated_data):
        from ar_client.apis.appliances_api import AppliancesApi
        """
        Update and return an existing `Cluster` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.public_key = validated_data.get('public_key', instance.public_key)
        instance.private_key = validated_data.get('private_key', instance.private_key)
        instance.has_password = validated_data.get('has_password', instance.has_password)

        user_id = validated_data.get('user_id', instance.user.id)
        if user_id is not None:
            user = Cluster.objects.filter(id=user_id).first()
            instance.user = user

        appliance_name = validated_data.get('appliance', instance.appliance)
        if appliance_name is not None:
            appliance = AppliancesApi().appliances_name_get(name=appliance_name)
            instance.appliance = appliance

        if instance.name != "" and instance.private_key != "" and instance.public_key != "":
            instance.save()
        return instance


class HostSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=100, allow_blank=True, default='')
    is_master = serializers.BooleanField(default=False)
    instance_id = serializers.CharField(max_length=100, allow_blank=True, default='')
    keypair = serializers.CharField(max_length=100, allow_blank=True, default='')
    instance_ip = serializers.CharField(max_length=100, allow_blank=True, default='')

    # Relationships
    cluster_id = serializers.IntegerField(read_only=True)

    def create(self, validated_data):
        """
        Create and return a new `Host` instance, given the validated data.
        """
        return Host.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Host` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.site = validated_data.get('site', instance.site)
        instance.instance_id = validated_data.get('instance_id', instance.instance_id)
        instance.keypair = validated_data.get('keypair', instance.keypair)
        instance.instance_ip = validated_data.get('instance_ip', instance.keypair)

        cluster_id = validated_data.get('cluster_id', instance.cluster.id)
        if cluster_id is not None:
            cluster = Cluster.objects.filter(id=cluster_id).first()
            instance.cluster = cluster

        if instance.name != "" and instance.site != "" and instance.instance_id != "":
            instance.save()
        return instance
