#!/usr/bin/env python

import logging
import os
import sys

from core.mister_hadoop import MisterHadoop
from novaclient.v2 import client

logging.basicConfig(level=logging.INFO)

parameters = {}
from jinja2 import Environment, FileSystemLoader

PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, '../templates')),
    trim_blocks=False)

experiment_parameters = {
    # "image_name": "CC-CENTOS-hadoop-feb2a35b-efbe-4cc3-8d86-4d72293b4965",
    "image_name": "CC-CENTOS-mongodb-0f1d6092-32e1-4de7-b0f0-b517ef3d883e",
    "flavor_name": "m1.medium",
    "network_label": "ext-net",
    "use_public_network": True,
    "keypair_name": "MySshKey",
    "instance_name_pattern": "hadoop-%s",
    "user": "cc",
    "root_user": "root",
    "cluster_type": "hadoop"
}

client = None

def listenToRequest(nova_client):
    print "Listening to Requests ..."
    first_instance = True
    mister_cluster = MisterHadoop(nova_client)
    while True:
        char = sys.stdin.read(1)
        request = {
            "operation": "add"
        }
        if (request["operation"] == "add"):
            # instance = self.provision_new_instance()
            if first_instance:
                mister_cluster.add_node_to_cluster(master=self.instances[0], is_master=False)
            else:
                mister_cluster.add_node_to_cluster(master=None, is_master=True)

            first_instance = False


if __name__ == "__main__":
    from conf.secret import secret

    parameters = {
        'OS_AUTH_URL': "https://openstack.tacc.chameleoncloud.org:5000/v2.0",
        'OS_TENANT_NAME': "FG-392",
        'OS_USERNAME': "jpastor",
        'OS_PASSWORD': secret["password"],
        'OS_REGION_NAME': "RegionOne",
        'OS_PROJECT_ID': "FG-392"
    }
    required_env_vars = ['OS_AUTH_URL', 'OS_TENANT_NAME', 'OS_USERNAME', 'OS_PASSWORD', 'OS_REGION_NAME']

    import novaclient

    with novaclient.v2.client.Client(parameters["OS_USERNAME"], parameters["OS_PASSWORD"], parameters["OS_PROJECT_ID"],
                                     parameters["OS_AUTH_URL"]) as nova:
        client = nova

    listenToRequest(nova)
