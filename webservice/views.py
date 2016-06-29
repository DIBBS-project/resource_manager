from django.shortcuts import render
from webservice.models import Job, Execution, Token
from webservice.serializers import JobSerializer

from django.views.decorators.csrf import csrf_exempt

from rest_framework.parsers import JSONParser
from django.http import HttpResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.mister_hadoop import MisterHadoop
from core.mister_fs import MisterFs
from core.mister_hdfs import MisterHdfs

from django.utils.encoding import smart_str
import logging

from lib.views_decorators import *


def index(request):
    files = []
    return render(request, "index.html", {"files": files})


mister_hadoop = MisterHadoop()
mister_fs = MisterFs()
mister_hdfs = MisterHdfs()

# Get an instance of a logger
logger = logging.getLogger(__name__)


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


##############################
# Hadoop
##############################


@api_view(['GET', 'POST'])
@expect_apitoken
@token_authentication
@csrf_exempt
def job_list(request):
    """
    List all code snippets, or create a new site.
    """
    if request.method == 'GET':
        sites = Job.objects.all()
        serializer = JobSerializer(sites, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = JobSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
@expect_apitoken
@token_authentication
@csrf_exempt
def job_detail(request, pk):
    """
    Retrieve, update or delete a site.
    """
    try:
        site = Job.objects.get(pk=pk)
    except Job.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = JobSerializer(site)
        return Response(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = JobSerializer(site, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        site.delete()
        return HttpResponse(status=204)


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def run_hadoop_job(request, pk):
    if request.method == 'GET' or True:
        # Find the Hadoop job
        job = Job.objects.filter(id=pk).first()
        response = mister_hadoop.run_job(job.command, request.username)
        execution = Execution()
        execution.job = job
        execution.application_hadoop_id = response["application_hadoop_id"]
        execution.save()

        if job.callback_url:
            mister_hadoop.watch_for_end_jobs_and_callback(execution.application_hadoop_id, job.callback_url)

        return Response(
            {"status": "ok",
             "application_hadoop_id": execution.application_hadoop_id},
            status=200)


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def get_running_jobs(request):
    """
    Get runnin hadoop jobs.
    """

    if request.method == 'GET':
        jobs = mister_hadoop.get_running_jobs()
        return Response(jobs)


##############################
# FS
##############################


@api_view(['GET', 'DELETE'])
@expect_apitoken
@token_authentication
@csrf_exempt
def fs_file_detail(request, path=None):
    """
    Retrieve, update or delete an HDFS file.
    """

    # By default, a non-set path refers to the root path
    if path is None:
        path = ""

    if request.method == 'GET':
        response = mister_fs.list_files(path)
        files = response
        return Response(files)

    if request.method == 'DELETE':
        files = mister_fs.delete_file(path)
        return Response(files)


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def fs_delete_file(request, path):
    """
    Delete an FS file.
    """

    if request.method == 'GET':
        status = mister_fs.delete_file(path)
        return Response(status)


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def fs_delete_folder(request, path):
    """
    Delete an HDFS folder.
    """

    if request.method == 'GET':
        status = mister_fs.delete_file(path, is_folder=True)
        return Response(status)


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def create_fs_folder(request, path):
    """
    Create an FS folder.
    """

    if request.method == 'GET':
        status = mister_fs.create_folder(path)
        return Response(status)


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def run_file(request, path):
    """
    Create an FS folder.
    """

    if request.method == 'GET':
        return_code = mister_fs.run_file(path)
        http_status = 200 if (return_code == 0) else 500
        status = "ok" if (return_code == 0) else "ko"
        return Response({"status": status, "return_code": return_code}, status=http_status)


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def download_fs_file(request, path):
    """
    Download a FS file
    """

    if request.method == 'GET':
        filename = path.split("/")[-1]
        data = mister_fs.load_file(filename)
        response = HttpResponse(data)
        response[
            'Content-Disposition'] = 'attachment; filename=%s' % smart_str(
                path)
        response['X-Sendfile'] = smart_str(filename)
        return response

        return mister_hdfs.list_files(path)


@api_view(['POST'])
@expect_apitoken
@token_authentication
@csrf_exempt
def upload_fs_file(request, path):
    """
    Retrieve, update or delete an user.
    """

    if request.method == 'POST':
        filename = path.split("/")[-1]

        # Read content of the file
        file_content = request.data['data'].read()
        mister_fs.create_file(path, file_content)

        # Put the file on FS
        mister_hadoop.add_local_file_to_hdfs(path, filename, request.username)
        return Response({"status": "ok"}, status=201)


##############################
# HDFS
##############################


@api_view(['GET', 'DELETE'])
@expect_apitoken
@token_authentication
@csrf_exempt
def hdfs_file_detail(request, path=None):
    """
    Retrieve, update or delete an HDFS file.
    """

    # By default, a non-set path refers to the root path
    if path is None:
        path = ""

    if request.method == 'GET':
        response = mister_hdfs.list_files(path)

        # Check if the path contains anything
        if not "FileStatuses" in response:
            return Response(
                {"result": "error",
                 "type": "hdfs_error",
                 "msg": "file '/%s' does not exists" % (path)},
                status=404)

        # Check if the results contains files
        files = response["FileStatuses"]["FileStatus"] if len(
            response) > 0 else []

        # Send the response
        return Response(files)

    if request.method == 'DELETE':
        files = mister_hdfs.delete_file(path)
        return Response(files)

    elif request.method == 'DELETE':
        file.delete()
        return HttpResponse(status=204)


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def hdfs_delete_file(request, path):
    """
    Delete an HDFS file.
    """

    if request.method == 'GET':
        files = mister_hdfs.delete_file(path)
        return Response(files)


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def hdfs_delete_folder(request, path):
    """
    Delete an HDFS folder.
    """

    if request.method == 'GET':
        files = mister_hdfs.delete_file(path, is_folder=True)
        return Response(files)


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def create_hdfs_folder(request, path):
    """
    Create an HDFS folder.
    """

    if request.method == 'GET':
        mister_hadoop.create_hdfs_folder(path, request.username)
        return Response({"status": "ok"})


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def download_hdfs_file(request, hdfspath):
    """
    Download an HDFS file.
    """

    if request.method == 'GET':
        import uuid
        random_filename = str(uuid.uuid4())
        filename = hdfspath.split("/")[-1]

        mister_hadoop.collect_file_from_hdfs(hdfspath, random_filename)

        data = mister_fs.load_file(random_filename)
        response = HttpResponse(data)
        response[
            'Content-Disposition'] = 'attachment; filename=%s' % smart_str(
                filename)
        response['X-Sendfile'] = smart_str(random_filename)
        return response

        return mister_hdfs.list_files(hdfspath)


@api_view(['POST'])
@expect_apitoken
@token_authentication
@csrf_exempt
def upload_hdfs_file(request, hdfspath):
    """
    Upload an HDFS file.
    """

    if request.method == 'POST':

        # Read content of the file
        file_content = request.data['data'].read()
        import uuid
        tmp_filename = str(uuid.uuid4())
        # Update the local file
        mister_fs.create_file(tmp_filename, file_content)

        # Put the file on HDFS
        mister_hadoop.add_local_file_to_hdfs(hdfspath, tmp_filename, request.username)
        return Response({"status": "ok"}, status=201)


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def hdfs_copy_to_local(request, hdfspath, localpath):
    """
    Copy an HDFS file to a local path.
    """

    if request.method == 'GET':
        try:
            mister_hadoop.collect_file_from_hdfs(hdfspath, localpath, request.username)
        except:
            return Response({"status": "bad"}, status=404)

        return Response({"status": "ok"}, status=201)


@api_view(['GET'])
@expect_apitoken
@token_authentication
@csrf_exempt
def hdfs_merge_directory(request, hdfspath, localpath):
    """
    Merge files of an HDFS folder into a single local file.
    """

    if request.method == 'GET':
        try:
            mister_hdfs.merge_directory(hdfspath, localpath, request.username)
        except Exception as e:
            print(e)
            return Response({"status": "bad"}, status=404)

        return Response({"status": "ok"}, status=201)
