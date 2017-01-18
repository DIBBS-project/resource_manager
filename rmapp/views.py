# coding: utf-8
from __future__ import absolute_import, print_function

import json
import logging
import time
import uuid

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view
from rest_framework.decorators import detail_route
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
import urllib3.exceptions

from rmapp import remote
from rmapp.core.mister_cluster import MisterClusterHeat as MisterClusterImplementation
# from rmapp.core.mister_cluster import MisterClusterNova as MisterClusterImplementation
from rmapp.models import Cluster, Host, Profile, Credential, ClusterCredential
from rmapp.serializers import UserSerializer, ClusterSerializer, HostSerializer, ProfileSerializer, CredentialSerializer

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Index that provides a description of the API
def index(request):
    clusters = Cluster.objects.all()
    return render(request, "index.html", {"clusters": clusters})


##############################
# Cluster management
##############################


class ClusterViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        data2 = {}
        for key in request.data:
            data2[key] = request.data[key]
        data2[u'user'] = request.user.id

        # Retrieve site information with the Appliance Registry API (check for existence)
        appliance = remote.appliances_name(data2[u'appliance'])

        serializer = self.get_serializer(data=data2)
        serializer.is_valid(raise_exception=True)

        cluster = Cluster()
        cluster.appliance = appliance.name
        cluster.user_id = request.user.id
        cluster.name = "%s_%s" % (appliance.name, uuid.uuid4())
        cluster.hints = data2["hints"]
        if "targeted_slaves_count" in data2:
            cluster.targeted_slaves_count = data2["targeted_slaves_count"]
        cluster.save()

        if cluster.targeted_slaves_count > 0:
            mister_cluster = MisterClusterImplementation()
            mister_cluster.resize_cluster(cluster, new_size=cluster.targeted_slaves_count)

        serializer = ClusterSerializer(cluster)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        if "pk" in kwargs:
            cluster_id = kwargs["pk"]
            candidates = Cluster.objects.filter(id=cluster_id)
            if len(candidates) > 0:
                cluster = candidates[0]
                # Remove all cluster's host
                for host in cluster.host_set.all():
                    host.delete()
                mister_cluster = MisterClusterImplementation()
                try:
                    mister_cluster.delete_cluster(cluster)
                except:
                    logging.error("an error occured while deleting resources of cluster %s. It seems that this cluster was non functional." % (cluster.id))
                    pass

        # clusters = Cluster.objects.all()
        # serializer = ClusterSerializer(clusters)
        # return Response(serializer.data, status=status.HTTP_201_CREATED)
        return viewsets.ModelViewSet.destroy(self, request, args, kwargs)

    @detail_route(methods=['post'])
    def new_account(self, request, pk):
        """
        Create a new temporary user account on an existing cluster.
        """
        try:
            cluster = Cluster.objects.get(id=pk)
        except Cluster.DoesNotExist:
            return Response(
                {"detail": "Could not find a cluster with id '{}'".format(pk)},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.dibbs_user is None:
            return Response({'detail': 'DIBBs username not provided'}, status=400)

        try:
            cc = ClusterCredential.objects.get(cluster=cluster, dibbs_user=request.dibbs_user)
        except ClusterCredential.DoesNotExist:
            cc = None
        else:
            try:
                user_creds = json.loads(cc.resource_credentials)
            except ValueError:
                logger.warning('corrupt JSON in database')
            else:
                if user_creds:
                    return Response(user_creds)

        master_node_ip = cluster.master_node.instance_ip
        service_url = 'http://{}:{}'.format(master_node_ip, 8012)

        try:
            result = remote.actions_new_account(service_url)
        except Exception:
            logging.info(
                "service located at '{}' does not seem to be ready, "
                "waiting 5 seconds before retrying".format(service_url))
            return Response(
                {"detail": "The cluster is not ready yet"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response = {
            "username": result.username,
            "password": result.password
        }

        if cc is None:
            # create new
            ClusterCredential.objects.create(
                cluster=cluster,
                dibbs_user=request.dibbs_user,
                resource_credentials=json.dumps(response)
            )
        else:
            # was corrupt; attempt to resave
            cc.resource_credentials = json.dumps(response)
            cc.save()

        return Response(response, status=201)

    @detail_route(methods=['post'])
    def add_host(self, request, pk):
        """
        Add a new host on an existing cluster.
        """

        clusters = Cluster.objects.filter(id=pk).all()
        if len(clusters) == 0:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        cluster = clusters[0]

        add_host(cluster)

        serializer = ClusterSerializer(cluster)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @detail_route(methods=['post'])
    def remove_host(self, request, pk):
        """
        Remove an host from an existing cluster.
        """

        clusters = Cluster.objects.filter(id=pk).all()
        if len(clusters) == 0:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        cluster = clusters[0]

        remove_host(cluster)

        serializer = ClusterSerializer(cluster)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


##############################
# Host management
##############################

def add_host(cluster):
    mister_cluster = MisterClusterImplementation()
    cluster.targeted_slaves_count += 1
    cluster.save()
    result = mister_cluster.resize_cluster(cluster, new_size=cluster.targeted_slaves_count)
    return result


def remove_host(cluster):
    mister_cluster = MisterClusterImplementation()
    cluster.targeted_slaves_count -= 1
    cluster.save()
    result = mister_cluster.resize_cluster(cluster, new_size=cluster.targeted_slaves_count)
    return result


class HostViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = Host.objects.all()
    serializer_class = HostSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        data = JSONParser().parse(request)

        data2 = {}
        for key in data:
            data2[key] = data[key]
        data2[u'user'] = request.user.id

        cluster_candidates = Cluster.objects.filter(id=data2["cluster_id"])
        if len(cluster_candidates) > 0:
            cluster = cluster_candidates[0]
            host = add_host(cluster)

        return Response({"host_id": host.id}, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        if "pk" in kwargs:
            host_id = kwargs["pk"]
            candidates = Host.objects.filter(id=host_id)
            if len(candidates) > 0:
                host = candidates[0]
                result = remove_host(host)
                if not result:
                    raise Exception("Could not delete instance associated to host %s" % (host_id))

        return viewsets.ModelViewSet.destroy(self, request, args, kwargs)


##############################
# Credentials management
##############################


class CredentialViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = Credential.objects.all()
    serializer_class = CredentialSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        data2 = {}
        for key in request.data:
            data2[key] = request.data[key]
        data2[u'user'] = request.user.id

        serializer = self.get_serializer(data=data2)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@api_view(['GET'])
def credentials_for_user(request, user_id):
    try:
        creds = Credential.objects.filter(user_id=user_id)
        response = []
        for cred in creds:
            response.append(CredentialSerializer(cred))
    except:
        return Response({"error": "Cannot find user %s" % user_id}, status=404)
    return Response(response)


##############################
# User management
##############################


class UserViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        data2 = {}
        for key in request.data:
            data2[key] = request.data[key]
        data2[u'credentials'] = []
        data2[u'clusters'] = []
        serializer = self.get_serializer(data=data2)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


@api_view(['GET'])
def rsa_public_key(request, user_id):
    from Crypto.PublicKey import RSA
    try:
        profile = Profile.objects.get(user=user_id)
        key = RSA.importKey(profile.rsa_key)
        public_key_str = key.publickey().exportKey()
    except:
        return Response({"error": "Cannot find user %s" % user_id}, status=404)
    return Response({"public_key": public_key_str})


def get_certificate(request, pk):
    user = get_user_model().objects.filter(id=pk)
    if user:
        tmp_folder = "/tmp/%s" % user[0].username
        from rmapp.core.authenticator import Authenticator
        authenticator = Authenticator()
        certificate = authenticator.generate_public_certification(tmp_folder)
        return HttpResponse(certificate)
    else:
        return HttpResponse("Could not generate certificate")
