# coding: utf-8
from __future__ import absolute_import, print_function

import logging

from django.conf import settings
import heatclient
from keystoneauth1 import loading
from keystoneauth1 import session
from novaclient import client as novaclient
import yaml

from common_dibbs.django import relay_swagger
import requests

from rmapp import remote
from rmapp.core.authenticator import Authenticator
from rmapp.core.scheduling_policies import SimpleSchedulingPolicy as SchedulingPolicy
from rmapp.lib.common import *
from rmapp.models import Cluster, Host

logger = logging.getLogger(__name__)
authenticator = Authenticator()


def get_heatclient_from_credentials(full_credentials):
    import keystoneauth1.identity.generic as generic
    from keystoneauth1 import session as kssession
    import heatclient.client as heat_client
    assert full_credentials[u'site'].type == 'openstack' or full_credentials[u'site'].type == 'baremetal'

    os_auth_url = full_credentials[u'site'].contact_url
    credentials = full_credentials[u'credentials']
    username = credentials[u'username']
    password = credentials[u'password']
    project = credentials[u'project']

    kwargs = {
        'username': username,
        'user_id': "",
        'user_domain_id': "",
        'user_domain_name': "",
        'password': password,
        'auth_url': os_auth_url,
        'project_id': "",
        'project_name': project,
        'project_domain_id': "",
        'project_domain_name': "",
    }
    keystone_session = kssession.Session(verify=True, cert="", timeout=None)
    keystone_auth = generic.Password(**kwargs)

    kwargs = {
        'auth_url': os_auth_url,
        'session': keystone_session,
        'auth': keystone_auth,
        'service_type': "orchestration",
        'endpoint_type': "publicURL",
        'region_name': "",
        'username': username,
        'password': password,
        'include_pass': False
    }

    heatclient = heat_client.Client("1", **kwargs)
    return heatclient


def get_novaclient_from_credentials(full_credentials):
    # assert full_credentials[u'site'].type == 'openstack'
    os_auth_url = full_credentials[u'site'].contact_url
    credentials = full_credentials[u'credentials']
    username = credentials[u'username']
    password = credentials[u'password']
    project = credentials[u'project']

    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(auth_url=os_auth_url,
                                    username=username,
                                    password=password,
                                    project_name=project)
    sess = session.Session(auth=auth)
    logger.info("Calling nova client with %s %s %s %s", username, password, project, os_auth_url)
    return novaclient.Client('2', session=sess)


class MisterClusterInterface(object):

    # def generate_clusters_keypairs(self, cluster):
    #     raise not NotImplemented

    def resize_cluster(self, cluster, new_size=1, master=None):
        raise not NotImplemented

    def delete_node_from_cluster(self, cluster):
        raise not NotImplemented

    def delete_cluster(self, cluster):
        raise not NotImplemented


class MisterClusterHeat(MisterClusterInterface):

    def resize_cluster(self, cluster, new_size=1, master=None):
        logger.info("Starting the resize of the cluster <%s>" % (cluster.id))

        cluster_db_object = cluster
        cluster_db_object.status = "Adding a node"
        cluster_db_object.save()

        appliance = remote.appliances_name(cluster_db_object.appliance)

        sites = remote.sites()
        implementations = remote.appliance_implementations()
        clusters = Cluster.objects.all()

        appliance_impl_name = cluster_db_object.appliance_impl
        common_appliance_impl_name = cluster_db_object.common_appliance_impl

        if appliance_impl_name == "" or common_appliance_impl_name == "":
            # TODO: Change the signature of this function, no need for all this information as well as common_a_impl
            # HINT INSERTION: Add a hint to this function to help to chose the right site
            (appliance_impl, common_appliance_impl, credential) = SchedulingPolicy().choose_appliance_implementation(
                appliance,
                implementations,
                sites,
                clusters,
                cluster_db_object.hints
            )
            appliance_impl_name = appliance_impl.name
            common_appliance_impl_name = common_appliance_impl.name
            cluster_db_object.appliance_impl = appliance_impl_name
            cluster_db_object.common_appliance_impl = common_appliance_impl_name
            cluster_db_object.credential = credential.name
            cluster_db_object.save()
        else:
            appliance_impl = remote.appliances_impl_name_get(appliance_impl_name)
            common_appliance_impl = remote.appliances_impl_name_get(common_appliance_impl_name)

        if appliance_impl is None or common_appliance_impl is None:
            cluster_db_object.status = "Error"
            cluster_db_object.save()
            raise Exception("Could not find an implementation of the given appliance/")

        full_credentials = cluster_db_object.get_full_credentials()
        if full_credentials is None:
            # TODO: Fail more gracefully
            raise Exception("No credentials for the selected site!")
        heat_client = get_heatclient_from_credentials(full_credentials)

        #is_master = cluster_db_object.get_master_node() is None
        try:
            cluster_db_object.master_node
        except Host.DoesNotExist:
            is_master = False
        else:
            is_master = True

        if is_master:
            cluster_db_object.status = "Adding master node"
        else:
            cluster_db_object.status = "Adding a slave node"
        cluster_db_object.save()

        tmp_folder = "/tmp/cluster_%s" % (cluster_db_object.uuid)

        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        # Generating Heat template
        logger.info("Generating Heat template")
        prepare_node_path = "%s/heat_template.yaml" % (tmp_folder)
        jinja_variables = {
            "infrastructure_type": full_credentials[u'site'].type
        }
        template_str = generate_script_from_appliance_registry(appliance_impl_name, "heat_template", prepare_node_path, jinja_variables)
        logger.info("Heat template has been generated")

        nc = get_novaclient_from_credentials(full_credentials)
        logger.info("Created a nova client object")

        networks = filter(lambda n: n.label != "ext-net", nc.networks.list())
        logger.info("Found the available networks: %s" % (networks))

        if len(networks) == 0:
            logger.error("No network found :(")
            raise Exception("No network found :(")

        network_name = networks[0].label
        logger.info("Found the network to use: %s" % (network_name))

        flavors = nc.flavors.list()
        flavor_name = flavors[0].name
        logger.info("Found the flavor to use: %s" % (flavor_name))

        r = requests.get('https://ipv4.jsonip.com/')
        my_public_ip = r.json()['ip']

        logger.info("Preparing the creation of a new Heat stack")
        heat_environment = {
            "parameters": {
                "cluster_size": new_size,
                "image_name": "CENTOS-7-HADOOP",
                "user_name": "root",
                "flavor_name": flavor_name,
                "network_name": network_name,
                "allowed_ip": "%s/32" % my_public_ip,
            }
        }
        if full_credentials[u'site'].type == "baremetal":
            heat_environment["parameters"]["reservation_id"] = eval(cluster.hints)["lease_id"]

        template_as_dict = yaml.load(template_str)
        if "heat_template_version" in template_as_dict and type(template_as_dict["heat_template_version"]) is not str:
            template_as_dict["heat_template_version"] = "2015-04-30"

        try:
            heat_template_data = {
                "stack_name": cluster.name,
                "disable_rollback": True,
                "parameters": {},
                "template": template_as_dict,
                "files": {},
                "environment": heat_environment
            }
            response = heat_client.stacks.create(**heat_template_data)
            stack_id = response["stack"]["id"] if "stack" in response and "id" in response["stack"] else None
        except heatclient.exc.HTTPConflict:
            heat_template_data = {
                "stack_id": cluster.name,
                "parameters": {},
                "template": template_as_dict,
                "files": {},
                "environment": heat_environment
            }
            # The stack already exist, we only need to update it
            logger.info("An existing Heat stack has been detected, I will only update it")

            continue_to_wait = True
            while continue_to_wait:
                continue_to_wait = False
                try:
                    heat_client.stacks.update(**heat_template_data)
                except Exception as e:
                    continue_to_wait = all(map(lambda s: s in e.message, ["has an action", "in progress"]))
                    logger.info("Heat conflict detected, waiting 2 more seconds")
                    time.sleep(2)
            stack_id = cluster.name

        if stack_id is not None:
            resource_group = None
            resource_group_is_not_ready = True
            while resource_group_is_not_ready:
                logger.info("Trying to find the resource_group containing slaves")
                fields = {
                    "stack_id": stack_id,
                    "nested_depth": None,
                    "with_detail": False,
                }
                stack_resources = heat_client.resources.list(**fields)
                resource_group = filter(lambda r: "ResourceGroup" in r.resource_type, stack_resources)[0]
                logger.info("This is how the resource_group containing slaves looks like: %s" % (resource_group))
                resource_group_is_not_ready = resource_group is None or resource_group.physical_resource_id == ""
                if resource_group_is_not_ready:
                    time.sleep(4)
            master_resource = filter(lambda r: "Server" in r.resource_type, stack_resources)[0]

            slave_resources = []
            if new_size > 0:
                while len(slave_resources) == 0:
                    logger.info("Trying to list resources of the resource_group")
                    slave_resources = heat_client.resources.list(heat_client.stacks.get(resource_group.physical_resource_id).id)
                    logger.info("I found those resources: %s" % (slave_resources))

            nova_client = get_novaclient_from_credentials(full_credentials)

            # Recreate the hosts of the cluster
            for host in cluster.host_set.all():
                host.delete()

            # Create a host for the master node
            master_host = Host()
            floating_ips = []
            logger.info("Setting logically the floating IP of the master node")
            while len(floating_ips) == 0:
                master_instance = nova_client.servers.find(id=master_resource.physical_resource_id)
                floating_ips = sum(map(lambda net: filter(lambda addr: addr["OS-EXT-IPS:type"]=="floating", master_instance.addresses[net]), master_instance.addresses), [])
            master_host.name = master_resource.resource_name
            master_host.instance_ip = floating_ips[0]["addr"]
            master_host.cluster_id = cluster.id
            master_host.is_master = True
            master_host.save()
            logger.info("The master node has the following IP: %s" % (floating_ips[0]["addr"]))

            # Create a host for each of the slaves
            last_slave = None
            for slave_resource in slave_resources:
                logger.info("Creating logically a slave resource")
                slave_host = Host()
                slave_host.name = slave_resource.resource_name
                slave_host.cluster_id = cluster.id
                slave_host.is_master = False
                slave_host.save()
                last_slave = slave_host

            logger.info("Updating slave count")
            cluster.current_slaves_count = new_size
            cluster.save()

        logger.info("MisterCluster has finished to deploy the stack")
        return last_slave

    def delete_cluster(self, cluster):
        logger.info("Starting the resize of the cluster <%s>" % (cluster.id))

        full_credentials = cluster.get_full_credentials()
        if full_credentials is None:
            # TODO: Fail more gracefully
            raise Exception("No credentials for the selected site!")

        hc = get_heatclient_from_credentials(full_credentials)
        hc.stacks.delete(cluster.name)

        return None
