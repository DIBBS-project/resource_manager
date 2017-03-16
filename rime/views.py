import json

from rest_framework import viewsets

from . import models
from . import openstack
from . import remote
from . import serializers

from .serializers import deobfuscate


class CredentialViewSet(viewsets.ModelViewSet):
    queryset = models.Credential.objects.all()
    serializer_class = serializers.CredentialSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClusterViewSet(viewsets.ModelViewSet):
    queryset = models.Cluster.objects.all()
    serializer_class = serializers.ClusterSerializer

    def perform_create(self, serializer):
        serializer.save(root_owner=self.request.user)

        #imp = remote.implementation(serializer.data['implementation'])
        imp = serializer.imp_data # volatile from validation...
        hot = imp['script']

        site = remote.site(imp['site'])

        credential = models.Credential.objects.get(id=serializer.data['credential'])
        credentials = deobfuscate(credential.credentials)
        credentials['auth_url'] = site['api_url']

        # keystone = openstack.keystone_session(credentials)
        # nc = openstack.nova_client(session=keystone)
        # print(nc.servers.list())


def get_or_create_resource(user, appliance: 'identifier', hints: dict = None):
    # find a cluster running the correct appliance
    # - also verify user has credentials on the site? soft privilege escalation hole
    # - validate those credentials? still poorly-controlled cross-talk between remote OS user privileges
    #   create/schedule resource creation (contact agent to generate credentials)

    # failing that, we need to create a cluster and put a resource on top of it

    # find an implementation that's the intersection of those that:
    # - implement the appliance (duh)
    # - were hinted (if provided)
    # - run on a site that the user has credentials to (limit sites and credentials if respectively hinted)
    if hints:
        if 'implementations' in hints:
            # fetch all implementation specs
            for imp_ref in hints['implementations']:
                imp = get_imp(imp_ref)
                ...

            # see if the
        if 'sites' in hints:
            pass

    else:
        pass
