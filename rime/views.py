import hashlib
import json
import logging

from django.conf import settings
import heatclient.exc as heat_exc
# from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from . import models
from . import openstack
from . import remote
from . import serializers


logger = logging.getLogger(__name__)


class CredentialViewSet(viewsets.ModelViewSet):
    queryset = models.Credential.objects.all()
    serializer_class = serializers.CredentialSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClusterViewSet(viewsets.ModelViewSet):
    queryset = models.Cluster.objects.all()
    serializer_class = serializers.ClusterSerializer

    def perform_create(self, serializer):
        cluster = serializer.save(root_owner=self.request.user)
        cluster.do_create()

    @detail_route(methods=['get'])
    def monitor(self, request, pk=None):
        cluster = self.get_object()
        # serializer = self.serializer_class(data=request.data)
        cb = cluster.monitor_transition()
        return Response({'result': repr(cb)})


class ResourceViewSet(viewsets.ViewSet):

    def create(self, request):
        try:
            hints = request.data['hints']
            impl = hints['implementation']
            cred = hints['credentials']
        except KeyError:
            logger.info('Invalid hints')
            return Response({'error': 'implementation/credentials not provided in hints'}, status=400)

        # search in existing resources
        try:
            cluster = models.Cluster.objects.get(implementation=impl)
        except models.Cluster.DoesNotExist:
            logger.info('No matching cluster found, building')
            try:
                credential = models.Credential.objects.get(id=cred)
            except models.Credential.DoesNotExist:
                return Response({'error': 'credential doesn\'t exist'}, status=400)
            if credential.user != request.user:
                return Response({'error': 'user does not have that credential'}, status=400)

            logger.info('Building cluster')
            cluster = models.Cluster.objects.create(
                root_owner=request.user,
                credential=credential,
                implementation=impl,
            )
            cluster.do_create()
        else:
            logger.info('Found existing matching cluster')

        resource = models.Resource(
            user=request.user,
            hints=json.dumps(hints),
            cluster=cluster,
        )
        resource.save()
        logger.info('Created resource {}'.format(resource.id))
        resource.async_create()
        serializer = serializers.ResourceSerializer(resource)
        return Response(serializer.data, status=201)

    # def list(self, request):
    #     pass

    def retrieve(self, request, pk=None):
        try:
            resource = models.Resource.objects.get(id=pk)
        except models.Resource.DoesNotExist:
            return Response(status=404)

        serializer = serializers.ResourceSerializer(resource)
        return Response(serializer.data)

    # def destroy(self, request, pk=None):
    #     pass


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
