#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render

from rpapp.models import User, Site, Cluster, Host, Token
from rpapp.models import User as OurUserClass
from rpapp.serializers import UserSerializer, SiteSerializer, ClusterSerializer, HostSerializer

from django.views.decorators.csrf import csrf_exempt

from rest_framework.parsers import JSONParser
from django.http import HttpResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from lib.common import *


from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework.decorators import authentication_classes

from lib.views_decorators import *

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Index that provides a description of the API
def index(request):
    clusters = Cluster.objects.all()
    return render(request, "index.html", {"clusters": clusters})


##############################
# User management
##############################


@api_view(['POST'])
@csrf_exempt
def register_new_user(request):
    username = request.POST.get("username")
    password = request.POST.get("password")
    logger.debug("will create user (%s, %s)" % (username, password))

    from django.contrib.auth.models import User
    try:
        user = User.objects.create_user(username=username, password=password)
        user.save()
    except:
        return Response({"status": "failed"})

    return Response({"status": "ok"})


@api_view(['GET'])
@expect_username
@expect_password
@user_authentication
@csrf_exempt
def generate_new_token(request):
    import uuid
    from django.contrib.auth.models import User

    try:
        user = User.objects.filter(username=request.username).first()

        token = Token()
        token.token = uuid.uuid4()
        token.username = request.username
        token.user_id = user.id
        token.save()

        return Response({"status": "ok", "token": token.token})
    except:
        return Response({"status": "failed"})


# Methods related to UserProfile
@api_view(['GET', 'POST'])
@csrf_exempt
def user_list(request):
    """
    List all users, or create a new user.
    """
    if request.method == 'GET':
        users = OurUserClass.objects.all()
        serializer = UserSerializer(users, many=True)
        for result in serializer.data:
            result["password"] = '********'
        return Response(serializer.data)
    # elif request.method == 'POST':
    #     data = JSONParser().parse(request)
    #     serializer = UserSerializer(data=data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=201)
    #     return Response(serializer.errors, status=400)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        required_fields = ["username", "password", "project"]
        missing_fields = []

        for required_field in required_fields:
            if required_field not in data:
                missing_fields += [required_field]

        if len(missing_fields) == 0:
            from rpapp import models
            user = OurUserClass()
            for field in data:
                setattr(user, field, data[field])
            user.save()
            generate_user_keypairs(user)
            return Response({"user_id": user.id, "api_token": user.api_token}, status=201)

        return Response({"missing_fields": missing_fields}, status=400)


@api_view(['GET', 'PUT', 'DELETE', 'PATCH'])
@expect_apitoken
@csrf_exempt
def user_detail(request, pk):
    """
    Retrieve, update or delete an user.
    """
    try:
        user = OurUserClass.objects.get(pk=pk)
    except User.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        user.password = "*" * len(user.password)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = UserSerializer(user, data=data)
        if serializer.is_valid():
            serializer.save()
            user.password = "*" * len(user.password)
            serializer = UserSerializer(user, data=data)
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        user.delete()
        return HttpResponse(status=204)

    elif request.method == 'PATCH':
        # A User is uploading an encrypted password file

        # Read content of the file

        user = OurUserClass.objects.filter(id=1).first()
        file_content = request.data['data'].read()
        tmp_folder = "tmp/%s" % user.username
        create_file("%s/password.txt" % tmp_folder, file_content)
        user.has_password = True
        user.save()

        return Response({"status": "ok"}, status=201)


# Methods related to Site
@api_view(['GET', 'POST'])
@csrf_exempt
def site_list(request):
    """
    List all code snippets, or create a new site.
    """
    if request.method == 'GET':
        sites = Site.objects.all()
        serializer = SiteSerializer(sites, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = SiteSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
@csrf_exempt
def site_detail(request, pk):
    """
    Retrieve, update or delete a site.
    """
    try:
        site = Site.objects.get(pk=pk)
    except Site.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = SiteSerializer(site)
        return Response(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = SiteSerializer(site, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        site.delete()
        return HttpResponse(status=204)


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
        from rpapp.core.mister_cluster import MisterCluster
        data = JSONParser().parse(request)
        required_fields = ["site_id", "appliance", "user_id", "name"]
        missing_fields = []

        for required_field in required_fields:
            if required_field not in data:
                missing_fields += [required_field]

        if len(missing_fields) == 0:
            from rpapp import models
            cluster = models.Cluster()
            for field in data:
                setattr(cluster, field, data[field])
            cluster.save()
            mister_cluster = MisterCluster()
            mister_cluster.generate_clusters_keypairs(cluster)
            return Response({"cluster_id": cluster.id}, status=201)

        return Response({"missing_fields": missing_fields}, status=400)


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
@expect_apitoken
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
        from rpapp.core.mister_cluster import MisterCluster
        data = JSONParser().parse(request)
        required_fields = ["cluster_id"]
        missing_fields = []

        for required_field in required_fields:
            if required_field not in data:
                missing_fields += [required_field]

        if len(missing_fields) == 0:
            from rpapp import models
            host = models.Host()
            for field in data:
                setattr(host, field, data[field])
            host.save()
            mister_cluster = MisterCluster()
            # cluster_id = data["cluster_id"]
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


if len(Cluster.objects.all()) == 0 and len(OurUserClass.objects.all()) == 0:
    from rpapp.fixtures import create_infrastructure
    create_infrastructure()


def get_certificate(request, pk):
    user = OurUserClass.objects.filter(id=pk)
    if user:
        tmp_folder = "tmp/%s" % (user[0].username)
        from rpapp.core.authenticator import Authenticator
        authenticator = Authenticator()
        certificate = authenticator.generate_public_certification(tmp_folder)
        return HttpResponse(certificate)
    else:
        return HttpResponse("Could not generate certificate")
