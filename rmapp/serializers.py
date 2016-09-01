from rest_framework import serializers
from models import Credential, Profile, Cluster, Host
import django.contrib.auth


class UserSerializer(serializers.ModelSerializer):
    credentials = serializers.PrimaryKeyRelatedField(many=True, queryset=Credential.objects.all())
    clusters = serializers.PrimaryKeyRelatedField(many=True, queryset=Cluster.objects.all())

    class Meta:
        model = django.contrib.auth.get_user_model()
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'credentials', 'clusters', 'is_staff', 'is_superuser', 'is_active',
                  'date_joined',
                  'password',)
        read_only_fields = ('id', 'credentials', 'clusters', 'is_staff', 'is_superuser', 'is_active',
                            'date_joined',)
        extra_kwargs = {
            'password': {'write_only': True}
        }


class CredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Credential
        fields = ('site_name', 'user', 'credentials',)
        extra_kwargs = {
            'credentials': {'write_only': True}
        }


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('user', 'rsa_key',)


class ClusterSerializer(serializers.ModelSerializer):
    # Custom fields
    host_ids = serializers.SerializerMethodField('cluster_hosts')
    hosts_ips = serializers.SerializerMethodField('cluster_hosts_ips')
    master_node_id = serializers.SerializerMethodField('cluster_master_node_id')
    master_node_ip = serializers.SerializerMethodField('cluster_master_node_ip')

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

    class Meta:
        model = Cluster
        fields = ('id', 'name', 'uuid', 'public_key', 'status',
                  'host_ids', 'hosts_ips', 'master_node_id', 'master_node_ip',
                  'appliance', 'appliance_impl', 'common_appliance_impl', 'master_node_id',)
        read_only_fields = ('id', 'host_ids', 'hosts_ips', 'master_node_id', 'master_node_ip',)


class HostSerializer(serializers.ModelSerializer):
    # # Relationships
    cluster_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Host
        fields = ('id', 'name', 'is_master', 'instance_id', 'instance_ip',
                  'cluster_id',)
        read_only_fields = ('id',)
