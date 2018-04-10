#!/usr/bin/python
# -*- coding: utf-8 -*-

# Temporarily spins up a droplet to download a torrent, grab the files, and then slurps them down from the droplet

import socket
from contextlib import closing
import digitalocean
import time
from digitalocean import SSHKey
from digitalocean import Action
import string
import sys
import json
import random
import paramiko
from scp import SCPClient
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.load_system_host_keys()
from Crypto.PublicKey import RSA

##########

Configuration = {}
with open('config.json') as json_data_file:
    Configuration = json.load(json_data_file)

##########

# Setup digitalocean manager

manager = digitalocean.Manager(token=Configuration['DO_TOKEN'])

# Construct runtime vars

ARIA_PRINT_INTERVAL = Configuration['ARIA_PRINT_INTERVAL']
T_FILE = sys.argv[1]
DOWNLOAD_FOLDER = Configuration['DOWNLOAD_FOLDER']

command_arr = ["apt update",
"apt install aria2 -y",
"mkdir -p download",
"cd download",
"aria2c --seed-time=0 --summary-interval={0} --show-console-readout=false \"{1}\"".format(ARIA_PRINT_INTERVAL,T_FILE) ]


# utils

def check_port(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as \
        sock:
        if sock.connect_ex((host, port)) == 0:
            return True
        else:
            return False


def progress(filename, size, sent):
    sys.stdout.write("%s\'s progress: %.2f%%   \r" % (filename,
                     float(sent) / float(size) * 100))


######

def download_dir(
    host,
    keyfile,
    dir,
    username='root',
    ):
    ssh.connect(host, username=username, key_filename=keyfile)
    with SCPClient(ssh.get_transport(), progress=progress) as scp:
        scp.get(dir, recursive=True)


def run_cmd_script(
    host,
    keyfile,
    command,
    username='root',
    ):
    ssh.connect(host, username=username, key_filename=keyfile)
    (stdin, stdout, stderr) = ssh.exec_command(command)
    stdin.close()
    for line in iter(lambda : stdout.readline(2048), ''):
        sys.stdout.flush()
        print line
    ssh.close()


def upload_ssh_key(file_pub_name, hostname):
    user_ssh_key = open(file_pub_name).read()
    key = SSHKey(token=Configuration['DO_TOKEN'], name=hostname,
                 public_key=user_ssh_key)
    key.create()
    print 'Uploaded Keypair'
    return key.id


def gen_key(privname='private.pem', pubname='public.pem'):
    key = RSA.generate(1024)
    f = open(privname, 'wb')
    f.write(key.exportKey('PEM'))
    f.close()
    pubkey = key.publickey()
    f = open(pubname, 'wb')
    f.write(pubkey.exportKey('OpenSSH'))
    print 'Created Keypair'
    f.close()


def generate_new_server():
    random_droplet_name = ''.join(random.choice(string.ascii_uppercase
                                  + string.digits) for _ in range(20))
    gen_key(random_droplet_name + '_private.pem', random_droplet_name
            + '_public.pem')
    keyid = upload_ssh_key(random_droplet_name + '_public.pem',
                           random_droplet_name)
    print 'Creating droplet named ' + random_droplet_name
    drop = digitalocean.Droplet(
        region=Configuration['MACHINE_CONFIG']['REGION'],
        size_slug=Configuration['MACHINE_CONFIG']['TYPE'],
        name=random_droplet_name,
        ssh_keys=[keyid],
        image=Configuration['MACHINE_CONFIG']['IMAGE'],
        backups=False,
        token=Configuration['DO_TOKEN'],
        )
    drop.create()
    action = Action(id=drop.action_ids[0], token=drop.token,
                    droplet_id=drop.id)
    action.load()
    action.wait(5)
    dropinfo = drop.load()
    return (drop, dropinfo)

def main_function():
    (dodroplet, dropinfo) = generate_new_server()
    print dropinfo.ip_address
    time.sleep(Configuration['WAIT_TIME'])
    while check_port(dropinfo.ip_address, 22) == False:
        time.sleep(3)
    print 'Droplet is Up!'
    cmd= 'apt update && apt install aria2 -y && mkdir download && cd download && aria2c --seed-time=0 \"' + T_FILE + '\"'
    print('executing' + cmd)
    run_cmd_script(dodroplet.ip_address, dodroplet.name + '_private.pem', cmd)
    print 'Files Downloaded To Droplet'
    download_dir(dodroplet.ip_address, dodroplet.name + '_private.pem',
                 '/root/{0}/'.format(DOWNLOAD_FOLDER))
    print 'Downloaded Locally! to ' + DOWNLOAD_FOLDER
    print 'Nuking the droplet!'
    dodroplet.destroy()
    print 'K Thx Bye!'


main_function()
