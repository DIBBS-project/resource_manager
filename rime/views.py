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

        template = cluster.template
        parameters = {
            'network_name': openstack.get_network(cluster.nova_client),
            'allowed_ip': settings.PUBLIC_IP + '/32', # only allow the LL controller to access the agents
        }
        # parameters.update(cluster.hints)
        logger.info('Stack parameters: {}'.format(json.dumps(parameters)))

        stack = {
            'stack_name': 'LL-{}'.format(cluster.id),#cluster.name,
            'template': cluster.template,
            'environment': {
                'parameters': parameters
            },
            'files': {},
            'parameters': {},
            'disable_rollback': True,
        }
        try:
            response = cluster.heat_client.stacks.create(**stack)
        except heat_exc.HTTPBadRequest as e:
            cluster.delete()
            raise

        logger.info('Created stack {}'.format(response['stack']['id']))

        cluster.remote_id = response['stack']['id']
        cluster.save()

    @detail_route(methods=['get'])
    def monitor(self, request, pk=None):
        cluster = self.get_object()
        # serializer = self.serializer_class(data=request.data)
        cb = cluster.monitor_transition()
        return Response({'result': repr(cb)})


class ResourceViewSet(viewsets.ViewSet):
    def create(self, request):
        pass

    def list(self, request):
        pass

    def retrieve(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass


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
