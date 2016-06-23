#!/usr/bin/env python

import logging
import os
import sys
import time
import paramiko
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(level=logging.INFO)

parameters = {}

PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, '../../templates')),
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


def detect_floating_ip_from_instance(instance):
    network_name = instance.networks.keys()[0]
    floating_ips = filter(lambda ip: ip[u'OS-EXT-IPS:type'] == u"floating", instance.addresses[network_name])

    if not floating_ips:
        logging.error("Could not detect any floating IPs for the instance %s" % (instance))
        raise "Could not detect any floating IPs for the instance %s" % (instance)
    else:
        floating_ip = floating_ips[0][u'addr']
    return floating_ip


def update_hosts_file(instances, username, key_filename, tmp_folder=None):
    hosts = []
    for instance in instances:
        floating_ip = detect_floating_ip_from_instance(instance)
        name = instance.name
        hosts += [{"name": name, "floating_ip": floating_ip}]

    for instance in instances:
        floating_ip = detect_floating_ip_from_instance(instance)
        ssh_master = paramiko.SSHClient()
        ssh_master.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_master.connect(floating_ip, username=username, key_filename=key_filename)

        # Send new hosts file to the current instance
        remote_hosts = filter(lambda x: x["name"] != instance.name, hosts)
        update_hosts_file_path = "%s/hosts" % (tmp_folder) if tmp_folder else "tmp/hosts"
        generate_template_file("common/update_hosts_file.jinja2", update_hosts_file_path,
                               {"node_name": instance.name, "floating_ip:": floating_ip, "hosts": remote_hosts})

        sftp_master = ssh_master.open_sftp()
        sftp_master.put(update_hosts_file_path, 'update_hosts_file.sh')
        time.sleep(5)
        ssh_master.exec_command("bash update_hosts_file.sh")


def execute_ssh_cmd(ssh_connection, command):
    stdin, stdout, stderr = ssh_connection.exec_command(command+" 2>&1")
    for line in stdout:
        # Do stuff with line
        # print line
        sys.stdout.write(line)
    # print stdout.readlines()
    return True


def create_file(path, data):
    # Delete file if it already exists
    if os.path.exists(path):
        os.remove(path)
    englobing_folder = "/".join(path.split("/")[:-1])
    if not os.path.exists(englobing_folder):
        os.makedirs(englobing_folder)
    # Write data in a new file
    with open(path, "w+") as f:
        f.write(data)
    return True


def generate_user_keypairs(user):

    request_uuid = user.username
    tmp_folder = "tmp/%s" % (request_uuid)

    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)

    # Generate ssh key
    key_paths = generate_rsa_key(tmp_folder)

    # Generate API token for the project
    from rpapp.core.authenticator import Authenticator
    authenticator = Authenticator()
    certificate = authenticator.generate_public_certification(tmp_folder)
    user.security_certificate = certificate
    user.save()


def generate_rsa_key(path, bits=1024):
    """ code extracted from http://stackoverflow.com/questions/2466401/how-to-generate-ssh-key-pairs-with-python. """
    from os import chmod
    from Crypto.PublicKey import RSA

    key = RSA.generate(bits)

    private_key_path = "%s/private.key" % (path)
    public_key_path = "%s/public.key" % (path)

    with open(private_key_path, 'w') as content_file:
        chmod(private_key_path, 0600)
        content_file.write(key.exportKey('PEM'))
    pubkey = key.publickey()
    with open(public_key_path, 'w') as content_file:
        content_file.write(pubkey.exportKey('OpenSSH'))

    return {"public": public_key_path, "private": private_key_path}
