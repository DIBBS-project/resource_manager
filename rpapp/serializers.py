from rest_framework import serializers
from models import Site, User, Cluster, Host


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


class SiteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=100, allow_blank=False, default='KVM@TACC')
    os_auth_url = serializers.CharField(max_length=1000, allow_blank=False, default='KVM@TACC')

    # Custom fields
    cluster_ids = serializers.SerializerMethodField('site_clusters')

    def site_clusters(self, site):
        return map(lambda x: x.id, Cluster.objects.filter(site_id=site.id))

    def create(self, validated_data):
        """
        Create and return a new `Site` instance, given the validated data.
        """
        return Site.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Site` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.os_auth_url = validated_data.get('os_auth_url', instance.os_auth_url)

        if instance.name != "" and instance.os_auth_url != "":
            instance.save()
        return instance


class ClusterSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=100, allow_blank=False, default='')
    uuid = serializers.CharField(max_length=100, allow_blank=True, default='')
    # private_key = serializers.CharField(max_length=1000, allow_blank=True, default='')
    public_key = serializers.CharField(max_length=1000, allow_blank=True, default='')
    # has_password = serializers.BooleanField(default=False)

    # Relationships
    user_id = serializers.IntegerField(read_only=True)
    site_id = serializers.IntegerField(read_only=True)
    software_id = serializers.IntegerField(read_only=True)

    # Custom fields
    host_ids = serializers.SerializerMethodField('cluster_hosts')
    master_node_id = serializers.SerializerMethodField('cluster_master_node_id')
    master_node_ip = serializers.SerializerMethodField('cluster_master_node_ip')
    hosts_ips = serializers.SerializerMethodField('cluster_hosts_ips')
    software_name = serializers.SerializerMethodField('cluster_software_name')


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

    def cluster_software_name(self, cluster):
        return cluster.get_software_name()

    def create(self, validated_data):
        """
        Create and return a new `Cluster` instance, given the validated data.
        """
        return Cluster.objects.create(**validated_data)

    def update(self, instance, validated_data):
        from ar_client.apis.softwares_api import SoftwaresApi
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

        site_id = validated_data.get('site_id', instance.site.id)
        if site_id is not None:
            site = Site.objects.filter(id=site_id).first()
            instance.site = site

        software_id = validated_data.get('software_id', instance.software.id)
        if software_id is not None:
            # software = Software.objects.filter(id=software_id).first()
            software = SoftwaresApi().softwares_id_get(id=software_id)
            instance.software = software

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
