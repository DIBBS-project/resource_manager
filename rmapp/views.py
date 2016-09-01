#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render
import django.contrib.auth

from rmapp.models import Cluster, Host, Profile, Credential
from rmapp.serializers import UserSerializer, ClusterSerializer, HostSerializer, ProfileSerializer, CredentialSerializer

from rest_framework import viewsets, permissions, status

from django.views.decorators.csrf import csrf_exempt

from rest_framework.parsers import JSONParser
from django.http import HttpResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rmapp.core.mister_cluster import MisterCluster
from rest_framework.decorators import detail_route

import base64

from lib.views_decorators import *

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Index that provides a description of the API
def index(request):
    clusters = Cluster.objects.all()
    return render(request, "index.html", {"clusters": clusters})


def configure_basic_authentication(swagger_client, username, password):
    authentication_string = "%s:%s" % (username, password)
    base64_authentication_string = base64.b64encode(bytes(authentication_string))
    header_key = "Authorization"
    header_value = "Basic %s" % (base64_authentication_string, )
    swagger_client.api_client.default_headers[header_key] = header_value


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
        from ar_client.apis.appliances_api import AppliancesApi

        data2 = {}
        for key in request.data:
            data2[key] = request.data[key]
        data2[u'user'] = request.user.id

        # Retrieve site information with the Appliance Registry API (check for existence)
        appliance = AppliancesApi().appliances_name_get(name=data2[u'appliance'])

        serializer = self.get_serializer(data=data2)
        serializer.is_valid(raise_exception=True)

        cluster = Cluster()
        cluster.appliance = appliance.name
        cluster.user_id = request.user.id
        cluster.name = data2["name"]
        cluster.save()

        mister_cluster = MisterCluster()
        mister_cluster.generate_clusters_keypairs(cluster)

        serializer = ClusterSerializer(cluster)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @detail_route(methods=['post'])
    def new_account(self, request, pk):
        """
        Create a new temporary user account on an existing cluster.
        """
        from rmapp.rpa_client.apis import ActionsApi

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


##############################
# Host management
##############################


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

        host = Host()
        for field in data2:
            setattr(host, field, data2[field])
        host.save()

        mister_cluster = MisterCluster()
        if not ("action" in data and data["action"] == "nodeploy"):
            mister_cluster.add_node_to_cluster(host)
        return Response({"host_id": host.id}, status=status.HTTP_201_CREATED)


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
    from rmapp.rpa_client.apis import ActionsApi

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
