#!/usr/bin/env python

import logging
import os
import pycurl
import json
from io import BytesIO
import uuid
import time
import threading
import requests

logging.basicConfig(level=logging.INFO)
import subprocess
from subprocess import check_output

parameters = {}
from jinja2 import Environment, FileSystemLoader

PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, '../templates')),
    trim_blocks=False)

client = None


def generate_template(input_file, context):
    output = TEMPLATE_ENVIRONMENT.get_template(input_file).render(context)
    return output


def generate_template_file(input_file, output_file, context):
    output = generate_template(input_file, context)
    with open(output_file, "w") as f:
        f.write(output)
    return True


def call_rest(url, method="GET"):
    """ Inspired by:
    http://stackoverflow.com/questions/15453608/extract-data-from-a-dictionary-returned-by-pycurl
    """
    c = pycurl.Curl()
    data = BytesIO()

    if method == "GET":
        c.setopt(c.HTTPGET, 1)
    elif method == "POST":
        c.setopt(c.HTTPPOST, 1)
    elif method == "PUT":
        c.setopt(c.HTTPPUT, 1)
    elif method == "DELETE":
        c.setopt(pycurl.CUSTOMREQUEST, "DELETE")
    elif method == "PATCH":
        c.setopt(c.HTTPPATCH, 1)

    print("c.setopt(c.URL, %s)" % (url))

    c.setopt(c.URL, str(url))
    c.setopt(c.WRITEFUNCTION, data.write)
    c.perform()

    return json.loads(data.getvalue())


class MisterHadoop:

    def __init__(self, parameters=None):
        self.server_ip = "127.0.0.1"
        self.url_postfix = "http://%s:8088/ws/v1" % (self.server_ip)

    def call_whdfs(self, action, http_method):
        return call_rest("%s/%s" % (self.url_postfix, action), http_method)

    def add_local_file_to_hdfs(self, hdfs_path, local_path, user):
        input_file = "hadoop/add_local_file_to_hdfs.sh.jinja2"
        output_file = "tmp/add_local_file_to_hdfs.sh"
        context = {
            "hdfs_path": hdfs_path,
            "local_path": local_path,
            "user": user
        }
        generate_template_file(input_file, output_file, context)
        subprocess.call("bash %s" % (output_file), shell=True)
        pass

    def create_hdfs_folder(self, hdfs_path, user):
        input_file = "hadoop/create_hdfs_folder.sh.jinja2"
        output_file = "tmp/create_hdfs_folder.sh"
        context = {
            "hdfs_path": hdfs_path,
            "user": user
        }
        generate_template_file(input_file, output_file, context)
        subprocess.call("bash %s" % (output_file), shell=True)
        pass

    def _wait_for_end_jobs_and_callback(self, application_hadoop_id, callback_url):
        wait_for_end_of_execution = True
        while wait_for_end_of_execution:
            print("waiting for the end of %s" % (application_hadoop_id))
            executions = filter(lambda x: x["id"] == application_hadoop_id, self.get_running_jobs())
            if executions:
                if executions[0]["progress"] == 100.0:
                    wait_for_end_of_execution = False
            time.sleep(1)
        print("calling %s" % (callback_url))
        # Inspired from: http://stackoverflow.com/questions/31826814/curl-post-request-into-pycurl-code
        data = {"application_hadoop_id": application_hadoop_id}
        response = requests.post(callback_url, json=data)
        print response.status_code
        pass

    def watch_for_end_jobs_and_callback(self, application_hadoop_id, callback_url):
        # Add a  thread that  will run  the function dedicated  to check  if the
        # execution of the job  is finished: when it is the case,  a call to the
        # callback_url will be made!
        t = threading.Thread(target=self._wait_for_end_jobs_and_callback,
                             args=(application_hadoop_id, callback_url),
                             kwargs={})
        t.setDaemon(True)
        t.start()

        pass

    def run_job(self, command, user):
        input_file = "hadoop/run_job.sh.jinja2"
        output_file = "tmp/run_job.sh"

        job_id = uuid.uuid4()
        stdout_file = "tmp/output_%s" % (job_id)

        context = {
            "command": command,
            "suffix": " 2>&1 | tee %s &" % (stdout_file),
            "user": user
        }
        generate_template_file(input_file, output_file, context)

        subprocess.call("bash %s" % (output_file), shell=True)

        application_hadoop_id = None
        pattern = "Submitted application"
        import time
        while application_hadoop_id is None:
            cmd = "grep '%s' %s | sed 's/.*Submitted application //g'" % (pattern, stdout_file)
            print("> %s" % cmd)
            try:
                out = os.popen(cmd).read().strip()
                if out != "":
                    application_hadoop_id = out
            except Exception as e:
                print e
                pass
            time.sleep(1)

        return {"application_hadoop_id": application_hadoop_id}

    def collect_file_from_hdfs(self, hdfs_name, local_path, user):
        input_file = "hadoop/collect_file_from_hdfs.sh.jinja2"
        output_file = "tmp/collect_file_from_hdfs.sh"
        context = {
            "hdfs_path": hdfs_name,
            "output_file": local_path,
            "user": user
        }
        generate_template_file(input_file, output_file, context)
        subprocess.call("bash %s" % (output_file), shell=True)

    def get_running_jobs(self):
        response = self.call_whdfs("cluster/apps", "GET")
        result = []
        if response["apps"]:
            result = response["apps"]["app"] if len(response) > 0 and "app" in response["apps"] else []
        return result


if __name__ == "__main__":
    pass
