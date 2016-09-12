#!/usr/bin/env python

from novaclient.v2 import client

from rmapp.conf import config
from rmapp.core.authenticator import Authenticator
from rmapp.lib.common import *
from scheduling_policies import DummySchedulingPolicy as SchedulingPolicy
import novaclient.exceptions as NovaExceptions
from settings import Settings
from common_dibbs.misc import configure_basic_authentication

logging.basicConfig(level=logging.INFO)

authenticator = Authenticator()


class MisterCluster:

    def __init__(self, parameters=None):
        self.nova_clients = {}

    # I have re-purposed code from: https://github.com/ChameleonCloud/testing/blob/master/tests/test_chi.py
    def provision_new_instance(self, nova_client, host, image_name, user_data=None):

        logging.info("Looking for the image")
        # image_name = config.configuration["image_name"]
        image = nova_client.images.find(name=image_name)
        if image is None:
            logging.error("Could not found the requested image (name=%s)" % (image_name))
            raise "Could not found the requested image (name=%s)" % (image_name)
        logging.info("Successfully found the image")

        logging.info("Looking for the flavor")
        flavor = None
        for flavor_name in config.configuration["flavor_names"]:
            try:
                flavor = nova_client.flavors.find(name=flavor_name)
            except NovaExceptions.NotFound:
                pass
            if flavor is not None:
                break
        if flavor is None:
            logging.error("Could not found the requested flavor (name=%s)" % (flavor_name))
            raise "Could not found the requested flavor (name=%s)" % (flavor_name)
        logging.info("Successfully found the flavor")

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
            time.sleep(1)

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
        logging.info("I will try to give a FloatingIp to %s" % (instance_name,))
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

        logging.info("Instance has been provisioned with id=%s" % (instance.id,))

        return instance, host

    @staticmethod
    def get_novaclient_from_credentials(full_credentials):
        import novaclient
        assert full_credentials[u'site'].type == 'openstack'
        os_auth_url = full_credentials[u'site'].contact_url
        credentials = full_credentials[u'credentials']
        username = credentials[u'username']
        password = credentials[u'password']
        project = credentials[u'project']
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
        from common_dibbs.clients.ar_client.apis.appliances_api import AppliancesApi
        from common_dibbs.clients.ar_client.apis.appliance_implementations_api import ApplianceImplementationsApi
        from common_dibbs.clients.ar_client.apis.sites_api import SitesApi
        from rmapp.models import Cluster
        logging.info("Starting addition of a node (%s) to the cluster <%s>" % (host.id, host.cluster_id))

        cluster_db_object = host.cluster
        cluster_db_object.status = "Adding a node"
        cluster_db_object.save()

        # Create a client for Appliances
        appliances_client = AppliancesApi()
        appliances_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
        configure_basic_authentication(appliances_client, "admin", "pass")

        # Create a client for ApplianceImplementations
        appliance_implementations_client = ApplianceImplementationsApi()
        appliance_implementations_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
        configure_basic_authentication(appliance_implementations_client, "admin", "pass")

        # Create a client for Sites
        sites_client = SitesApi()
        sites_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
        configure_basic_authentication(sites_client, "admin", "pass")

        appliance = appliances_client.appliances_name_get(cluster_db_object.appliance)

        sites = sites_client.sites_get()
        implementations = appliance_implementations_client.appliances_impl_get()
        clusters = Cluster.objects.all()

        appliance_impl_name = cluster_db_object.appliance_impl
        common_appliance_impl_name = cluster_db_object.common_appliance_impl

        if appliance_impl_name == "" or common_appliance_impl_name == "":
            # TODO: Change the signature of this function, no need for all this information as well as common_a_impl
            (appliance_impl, common_appliance_impl) = SchedulingPolicy().choose_appliance_implementation(
                appliance,
                implementations,
                sites,
                clusters
            )
            appliance_impl_name = appliance_impl.name
            common_appliance_impl_name = common_appliance_impl.name
            cluster_db_object.appliance_impl = appliance_impl_name
            cluster_db_object.common_appliance_impl = common_appliance_impl_name
            cluster_db_object.save()
        else:
            appliance_impl = appliance_implementations_client.appliances_impl_name_get(appliance_impl_name)
            common_appliance_impl = appliance_implementations_client.appliances_impl_name_get(common_appliance_impl_name)

        if appliance_impl is None or common_appliance_impl is None:
            cluster_db_object.status = "Error"
            cluster_db_object.save()
            raise Exception("Could not find an implementation of the given appliance/")

        full_credentials = cluster_db_object.get_full_credentials()
        if full_credentials is None:
            # TODO: Fail more gracefully
            raise Exception("No credentials for the selected site!")
        nova_client = self.get_novaclient_from_credentials(full_credentials)

        is_master = cluster_db_object.get_master_node() is None
        if is_master:
            cluster_db_object.status = "Adding master node"
        else:
            cluster_db_object.status = "Adding a slave node"
        cluster_db_object.save()

        logging.info("Is this new node a master node? %s" % (is_master,))

        request_uuid = cluster_db_object.uuid
        tmp_folder = "tmp/%s" % (request_uuid,)
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
        user_data = generate_script_from_appliance_registry(appliance_impl.name, "user_data", user_data_path, variables)
        logging.info("User data successfully generated!")

        logging.info("Calling 'provision_new_instance' to create an instance (%s)" % (host.name))

        # Provision an instance
        (instance, host) = self.provision_new_instance(nova_client, host, appliance_impl.image_name, user_data=user_data)

        logging.info("The instance has been created (%s)" % (host.name))

        if is_master:
            host.is_master = True
            host.save()
            logging.info("A master node of cluster <%s> has been elected" % (host.cluster_id))

        instances_ids = map(lambda x: x.instance_id, cluster_db_object.host_set.all())
        instances = map(lambda id: nova_client.servers.find(id=id), instances_ids)
        variables["nodes"] = instances

        floating_ip = detect_floating_ip_from_instance(instance)
        host.instance_ip = floating_ip
        host.save()
        logging.info("The new instance has now a floating IP (%s)" % (floating_ip))

        # Try to connect via SSH to the instance
        ok = False
        i = 0
        while (not ok) and i < 30:
            try:
                logging.info("Trying to establish a ssh connection to the new instance %s" % (i))
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(floating_ip, username=user, key_filename=key_paths["private"])
                logging.info("Ssh connection established!")
                ok = True
            except:
                time.sleep(3)
                i += 1
        logging.info("Updating hosts file of nodes %s" % (instances_ids))
        update_hosts_file(instances, user, key_paths["private"], common_appliance_impl_name, tmp_folder=tmp_folder)
        logging.info("Hosts file of nodes %s have been updated" % (instances_ids))

        variables["node_ip"] = floating_ip
        variables["node_name"] = instance.name

        if is_master:
            variables["is_master"] = True
            variables["master_ip"] = floating_ip
            variables["master_name"] = instance.name

        execute_ssh_cmd(ssh, "touch success")

        # Configure Node
        logging.info("Preparing the new node")
        prepare_node_path = "%s/prepare_node" % (tmp_folder)
        generate_script_from_appliance_registry(appliance_impl_name, "prepare_node", prepare_node_path, variables)

        sftp = ssh.open_sftp()
        sftp.put(prepare_node_path, 'prepare_node.sh')

        execute_ssh_cmd(ssh, "bash prepare_node.sh")

        logging.info("Node prepared!")

        # Configure cluster node
        logging.info("Configuring node to join the cluster")
        configure_node_path = "%s/configure_node" % tmp_folder
        generate_script_from_appliance_registry(appliance_impl_name, "configure_node", configure_node_path, variables)

        sftp = ssh.open_sftp()
        sftp.put(configure_node_path, 'configure_node.sh')
        execute_ssh_cmd(ssh, "bash configure_node.sh")

        logging.info("The node joined the cluster!")

        if not is_master:
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
            generate_script_from_appliance_registry(appliance_impl_name, "update_master_node",
                                                    update_master_node_path, variables)

            sftp_master = ssh_master.open_sftp()
            sftp_master.put(update_master_node_path, 'update_master_node.sh')
            # time.sleep(5)
            ssh_master.exec_command("bash update_master_node.sh")
            logging.info("Successfully updated the master node!")

        cluster_db_object.status = "IDLE"
        cluster_db_object.save()
        return True
