#!/usr/bin/env python
# -*- coding: utf-8 -*-

import django.contrib.auth
from common_dibbs.clients.ar_client.apis.appliances_api import AppliancesApi
from common_dibbs.clients.rpa_client.apis import ActionsApi
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view
from rest_framework.decorators import detail_route
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
import time
import urllib3.exceptions

from rmapp.core.mister_cluster import MisterClusterHeat as MisterClusterImplementation
# from rmapp.core.mister_cluster import MisterClusterNova as MisterClusterImplementation

from rmapp.models import Cluster, Host, Profile, Credential
from rmapp.serializers import UserSerializer, ClusterSerializer, HostSerializer, ProfileSerializer, CredentialSerializer
from settings import Settings
# import the logging library
import logging
from common_dibbs.misc import configure_basic_authentication
import uuid

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

        # Create a client for Appliances
        appliances_client = AppliancesApi()
        appliances_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
        configure_basic_authentication(appliances_client, "admin", "pass")

        # Retrieve site information with the Appliance Registry API (check for existence)
        appliance = appliances_client.appliances_name_get(name=data2[u'appliance'])

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

        clusters = Cluster.objects.filter(id=pk).all()
        if len(clusters) == 0:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        cluster = clusters[0]

        master_node_ip = cluster.get_master_node().instance_ip

        actions_api = ActionsApi()
        actions_api.api_client.host = "http://%s:8012" % (master_node_ip,)
        configure_basic_authentication(actions_api, "admin", "pass")

        try_account_creation = True
        while try_account_creation:
            try:
                result = actions_api.new_account_post()
                try_account_creation = False
            except:
                logging.info("service located at 'http://%s:8012' does not seem to be ready, waiting 5 seconds before retrying to contact it" % (master_node_ip,))
                time.sleep(5)

        response = {
            "username": result.username,
            "password": result.password
        }
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
    queryset = django.contrib.auth.get_user_model().objects.all()
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


@api_view(['POST'])
@csrf_exempt
def new_account(request, pk):
    """
    Create a new temporary user account on an existing cluster.
    """

    clusters = Cluster.objects.filter(id=pk).all()
    if len(clusters) == 0:
        return Response({}, status=status.HTTP_404_NOT_FOUND)
    cluster = clusters[0]

    master_node_ip = cluster.get_master_node().instance_ip

    actions_api = ActionsApi()
    actions_api.api_client.host = "http://%s:8012" % (master_node_ip,)
    configure_basic_authentication(actions_api, "admin", "pass")

    result = actions_api.new_account_post()

    response = {
        "username": result.username,
        "password": result.password
    }
    return Response(response, status=201)


def get_certificate(request, pk):
    user = django.contrib.auth.get_user_model().objects.filter(id=pk)
    if user:
        tmp_folder = "tmp/%s" % user[0].username
        from rmapp.core.authenticator import Authenticator
        authenticator = Authenticator()
        certificate = authenticator.generate_public_certification(tmp_folder)
        return HttpResponse(certificate)
    else:
        return HttpResponse("Could not generate certificate")
