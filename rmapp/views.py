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


class CredentialViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = Credential.objects.all()
    serializer_class = CredentialSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        from ar_client.apis.sites_api import SitesApi
        import crypto

        data2 = {}
        for key in request.data:
            data2[key] = request.data[key]
        data2[u'user'] = request.user.id

        # Retrieve site information with the Appliance Registry API (check for existence)
        SitesApi().sites_name_get(name=data2[u'site_name'])
        # Use the private key de temporarily decrypt and check that it gives JSON
        decrypted_credentials = crypto.decrypt_credentials(data2[u'credentials'], user_id=request.user.id)
        # TODO (someday): Check that the credentials are correct (or at least that all the information is provided)

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


# Methods related to Cluster
@api_view(['GET', 'POST'])
@csrf_exempt
def cluster_list(request):
    """
    List all clusters, or create a new cluster.
    """
    if request.method == 'GET':
        clusters = Cluster.objects.all()
        serializer = ClusterSerializer(clusters, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        from rmapp.core.mister_cluster import MisterCluster

        data2 = {}
        for key in request.data:
            data2[key] = request.data[key]
        data2['user_id'] = request.user.id

        required_fields = ["appliance", "user_id", "name"]
        missing_fields = []

        for required_field in required_fields:
            if required_field not in data2:
                missing_fields += [required_field]

        if len(missing_fields) == 0:
            from rmapp import models
            cluster = models.Cluster()
            for field in data2:
                setattr(cluster, field, data2[field])
            cluster.save()
            mister_cluster = MisterCluster()
            mister_cluster.generate_clusters_keypairs(cluster)
            serializer = ClusterSerializer(cluster)
            return Response(serializer.data, status=201)

        return Response({"missing_fields": missing_fields}, status=400)


# Methods related to Cluster
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


@api_view(['GET', 'PUT', 'DELETE'])
@csrf_exempt
def cluster_detail(request, pk):
    """
    Retrieve, update or delete a cluster.
    """
    try:
        cluster = Cluster.objects.get(pk=pk)
    except Cluster.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = ClusterSerializer(cluster)
        return Response(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = ClusterSerializer(cluster, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        cluster.delete()
        return HttpResponse(status=204)


# Methods related to Host
@api_view(['GET', 'POST', 'PATCH'])
@csrf_exempt
def host_list(request):
    """
    List all code snippets, or create a new host.
    """
    if request.method == 'GET':
        hosts = Host.objects.all()
        serializer = HostSerializer(hosts, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        from rmapp.core.mister_cluster import MisterCluster
        data = JSONParser().parse(request)
        required_fields = ["cluster_id"]
        missing_fields = []

        for required_field in required_fields:
            if required_field not in data:
                missing_fields += [required_field]

        if len(missing_fields) == 0:
            from rmapp import models
            host = models.Host()
            for field in data:
                setattr(host, field, data[field])
            host.save()
            mister_cluster = MisterCluster()
            # cluster_id = data["cluster_id"]
            if not ("action" in data and data["action"] == "nodeploy"):
                mister_cluster.add_node_to_cluster(host)
            return Response({"host_id": host.id}, status=201)

        return Response({"missing_fields": missing_fields}, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
@csrf_exempt
def host_detail(request, pk):
    """
    Retrieve, update or delete an host.
    """
    try:
        host = Host.objects.get(pk=pk)
    except Host.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = HostSerializer(host)
        return Response(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = HostSerializer(host, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        host.delete()
        return HttpResponse(status=204)


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
