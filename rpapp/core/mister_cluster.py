#!/usr/bin/env python

import logging
import os
import time

import paramiko
from novaclient.v2 import client
from rpapp.lib.common import *
from rpapp.conf import config
from rpapp.core.authenticator import Authenticator
import uuid

logging.basicConfig(level=logging.INFO)

authenticator = Authenticator()


class MisterCluster:

    def __init__(self, parameters=None):
        self.nova_clients = {}

    # I have re-purposed code from: https://github.com/ChameleonCloud/testing/blob/master/tests/test_chi.py
    def provision_new_instance(self, nova_client, host, user_data=None):

        # TODO: network_label is kind of hardcoded: it should be more generic!
        network_label = config.configuration["network_label"]
        network = nova_client.networks.find(label=network_label)
        if network is None:
            logging.error("Could not found the requested network (name=%s)" % (network_label))
            raise "Could not found the requested network (name=%s)" % (network_label)
        nics = [{'net-id': network.id}]

        # TODO: image_name is kind of hardcoded: it should be more generic!
        image_name = config.configuration["image_name"]
        image = nova_client.images.find(name=image_name)
        if image is None:
            logging.error("Could not found the requested image (name=%s)" % (image_name))
            raise "Could not found the requested image (name=%s)" % (image_name)

        # TODO: flavor_name is kind of hardcoded: it should be more generic!
        flavor_name = config.configuration["flavor_name"]
        flavor = nova_client.flavors.find(name=flavor_name)
        if flavor is None:
            logging.error("Could not found the requested flavor (name=%s)" % (flavor_name))
            raise "Could not found the requested flavor (name=%s)" % (flavor_name)

        # Boot an instance with the selected parameters
        logging.info("Preparing to boot a new nova instance")
        current_hosts_count = len(host.cluster.host_set.all())
        # instance_name = config["instance_name_pattern"] % (current_hosts_count)
        # instance_name = "%s_%s" % (cluster_db_object.name, current_hosts_count)
        instance_name = host.name if host.name != "" else "%s%s" % (host.cluster.name, current_hosts_count)
        instance_name = instance_name.lower()
        instance_name = ''.join([i for i in instance_name if i.isalnum()])
        logging.info("Booting a new nova instance with the following name: %s" % (instance_name))

        instance = nova_client.servers.create(instance_name, image, flavor, userdata=user_data)

        if host.name == "":
            host.name = instance_name
            host.save()
        host.instance_id = instance.id
        host.save()

        logging.info("Waiting for the instance %s to be active" % (instance_name))
        while instance.status != "ACTIVE":
            instance = nova_client.servers.find(id=instance.id)
            time.sleep(10)

        logging.info("The instance %s is now active!" % (instance_name))

        logging.info("Getting the FixedIp of instance %s" % (instance_name))
        networks_names = instance.networks.keys()
        fixed_ip = None
        if len(networks_names) > 0:
            network_candidate_name = networks_names[0]
            network_candidate_ips = instance.networks[network_candidate_name]
            if len(network_candidate_ips) > 0:
                fixed_ip = network_candidate_ips[0]
        logging.info("The FixedIp of instance %s is %s" % (instance_name, fixed_ip))

        if fixed_ip is None:
            raise Exception("could not find a network associated to the newly created instance.")

        # Provide a floating IP to the newly created instance
        logging.info("I will try to give a FloatingIp to %s" % (instance_name))
        get_an_available_floating_ip = lambda: nova_client.floating_ips.findall(instance_id=None)
        if get_an_available_floating_ip is None:
            logging.info("a new floating IP will be created for instance (%s)" % (instance.id))
            nova_client.floating_ips.create()
        while not get_an_available_floating_ip():
            logging.info("Waiting for a new floating IP to be available...")
            time.sleep(5)
        floating_ip = get_an_available_floating_ip()[0]
        logging.info("A floating IP (%s) is available for instance (%s)" % (floating_ip, instance.id))

        nova_client.servers.add_floating_ip(instance, floating_ip)
        logging.info("A floating IP (%s) has been associated to instance (%s)" % (floating_ip, instance.id))

        # Reload Instance
        instance = nova_client.servers.find(id=instance.id)

        logging.info("Instance has been provisionned with id=%s" % (instance.id))

        return (instance, host)

    def get_novaclient_associated_to_site(self, user, site):

        #if not site in self.nova_clients:
        import novaclient
        os_auth_url = site.contact_url
        username = user.username
        from rpapp.core.authenticator import Authenticator
        authenticator = Authenticator()
        password = authenticator.decrypt_password("tmp/%s" % (user.username))
        project = user.project
        novaclient = novaclient.v2.client.Client(username, password, project, os_auth_url)
        return novaclient

    def generate_clusters_keypairs(self, cluster):

        request_uuid = cluster.uuid
        tmp_folder = "tmp/%s" % (request_uuid)

        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        # Generate ssh key
        if not cluster.private_key and not cluster.public_key:
            logging.info("Generating a new pair (public_key, private_key) in %s" % (tmp_folder))
            key_paths = generate_rsa_key(tmp_folder)
        else:
            key_paths = {
                "public": "%s/public.key" % (tmp_folder),
                "private": "%s/private.key" % (tmp_folder)
            }
            if not os.path.exists(key_paths["public"]):
                with open(key_paths["public"], "w") as f:
                    f.write(cluster.public_key)
            if not os.path.exists(key_paths["private"]):
                with open(key_paths["private"], "w") as f:
                    f.write(cluster.private_key)

        # # Generate API token for the project
        # certificate = authenticator.generate_public_certification(tmp_folder)
        # cluster.security_certificate = certificate
        # cluster.save()

    def add_node_to_cluster(self, host, master=None):
        from rpapp.ar_client.apis.appliances_api import AppliancesApi
        from rpapp.ar_client.apis.sites_api import SitesApi
        logging.info("Starting addition of a node (%s) to the cluster <%s>" % (host.id, host.cluster_id))

        cluster_db_object = host.cluster
        appliance = AppliancesApi().appliances_name_get(cluster_db_object.appliance)
        targetted_site = SitesApi().sites_name_get(appliance.site)
        targetted_user = cluster_db_object.user
        nova_client = self.get_novaclient_associated_to_site(targetted_user, targetted_site)

        is_master = cluster_db_object.get_master_node() is None

        cluster_type = cluster_db_object.appliance

        logging.info("Is this new node a master node? %s" % (is_master))

        request_uuid = cluster_db_object.uuid
        tmp_folder = "tmp/%s" % (request_uuid)
        # user = host.cluster.user.username
        user = config.configuration["user"]

        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        logging.info("node will be configured with script from %s folder" % (tmp_folder))

        request_uuid = cluster_db_object.uuid
        tmp_folder = "tmp/%s" % (request_uuid)
        key_paths = {
            "public": "%s/public.key" % (tmp_folder),
            "private": "%s/private.key" % (tmp_folder)
        }
        with open(key_paths["public"], "r") as f:
            public_key = f.readline()
        with open(key_paths["private"], "r") as f:
            private_key = "".join(f.readlines())

        if not host.cluster.private_key:
            host.cluster.private_key = private_key
            host.cluster.save()

        if not host.cluster.public_key:
            host.cluster.public_key = public_key
            host.cluster.save()

        logging.info("private/public keys available for the instance")

        if is_master:
            cluster_db_object.public_key = public_key
            cluster_db_object.private_key = private_key
            cluster_db_object.save()
            logging.info("private/public keys uploaded to the cluster")

        # Generate script that will configure the node
        variables = {
            "public_key": public_key,
            "private_key": private_key,
            "is_master": is_master,
            "user": user,
        }

        if not is_master:
            logging.info("I search the master-node that will be configured with the new node")
            variables["is_master"] = False
            master_node = cluster_db_object.get_master_node()
            master_node_id = master_node.instance_id
            master = nova_client.servers.find(id=master_node_id)
            master_ip = master.networks[master.networks.keys()[0]][0]
            variables["master_ip"] = master_ip
            variables["master_name"] = master.name
            logging.info("I found the master-node that will be configured with the new node")

        logging.info("Creating user data for the instance")
        user_data_path = "%s/user_data" % (tmp_folder)

        logging.info("Retrieving the user_data template")
        # template = get_template_from_appliance_registry(cluster_type, "user_data")
        # user_data = generate_template("%s/user_data.jinja2" % cluster_type, variables)
        # generate_template_file("%s/user_data.jinja2" % cluster_type, user_data_path, variables)
        user_data = generate_script_from_appliance_registry(cluster_type, "user_data", user_data_path, variables)
        logging.info("User data successfully generated!")

        logging.info("Calling 'provision_new_instance' to create an instance (%s)" % (host.name))

        # Provision an instance
        (instance, host) = self.provision_new_instance(nova_client, host, user_data=user_data)

        logging.info("The instance has been created (%s)" % (host.name))

        if is_master:
            host.is_master = True
            host.save()
            logging.info("A master node of cluster <%s> has been elected" % (host.cluster_id))

        time.sleep(8)  # TODO: Replace this by a loop on Paramiko in update_hosts_file
        instances_ids = map(lambda x: x.instance_id, cluster_db_object.host_set.all())
        instances = map(lambda id: nova_client.servers.find(id=id), instances_ids)

        logging.info("Updating hosts file of nodes %s" % (instances_ids))
        update_hosts_file(instances, user, key_paths["private"], tmp_folder=tmp_folder)
        logging.info("Hosts file of nodes %s have been updated" % (instances_ids))

        floating_ip = detect_floating_ip_from_instance(instance)
        host.instance_ip = floating_ip
        host.save()
        logging.info("The new instance has now a floating IP (%s)" % (floating_ip))

        variables["node_ip"] = floating_ip
        variables["node_name"] = instance.name

        if is_master:
            variables["is_master"] = True
            variables["master_ip"] = floating_ip
            variables["master_name"] = instance.name

        # Giving time to the instance to fully startup
        time.sleep(2)

        # Try to connect to the instance
        logging.info("Trying to establish a ssh connection to the new instance")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(floating_ip, username=user, key_filename=key_paths["private"])
        logging.info("Ssh connection established!")

        execute_ssh_cmd(ssh, "touch success")

        # Configure Node
        logging.info("Preparing the new node")
        prepare_node_path = "%s/prepare_node" % (tmp_folder)
        #generate_template_file("%s/prepare_node.jinja2" % cluster_type, prepare_node_path, variables)
        generate_script_from_appliance_registry(cluster_type, "prepare_node", prepare_node_path, variables)

        sftp = ssh.open_sftp()
        sftp.put(prepare_node_path, 'prepare_node.sh')
        time.sleep(5)

        execute_ssh_cmd(ssh, "bash prepare_node.sh")

        logging.info("Node prepared!")

        # Configure cluster node
        logging.info("Configuring node to join the cluster")
        configure_node_path = "%s/configure_node" % tmp_folder
        # generate_template_file("%s/configure_node.jinja2" % cluster_type, configure_node_path, variables)
        generate_script_from_appliance_registry(cluster_type, "configure_node", configure_node_path, variables)

        sftp = ssh.open_sftp()
        sftp.put(configure_node_path, 'configure_node.sh')
        time.sleep(5)
        execute_ssh_cmd(ssh, "bash configure_node.sh")

        logging.info("The node joined the cluster!")

        if not is_master:
            time.sleep(30)
            # Updating master_node
            logging.info("Connecting to the master node")
            master_node_floating_ip = detect_floating_ip_from_instance(master)
            ssh_master = paramiko.SSHClient()
            ssh_master.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_master.connect(master_node_floating_ip, username=user, key_filename=key_paths["private"])
            logging.info("Successfully connected to the master node!")

            # Send files to the master node
            logging.info("Updating master node to take into account the new node")
            update_master_node_path = "%s/update_master_node" % (tmp_folder)
            # generate_template_file("%s/update_master_node.jinja2" % cluster_type, update_master_node_path, variables)
            generate_script_from_appliance_registry(cluster_type, "update_master_node",
                                                    update_master_node_path, variables)

            sftp_master = ssh_master.open_sftp()
            sftp_master.put(update_master_node_path, 'update_master_node.sh')
            time.sleep(5)
            ssh_master.exec_command("bash update_master_node.sh")
            logging.info("Successfully updated the master node!")

        return True
