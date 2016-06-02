#!/usr/bin/python

# The IP addressses of consul cluster members are not known at stack build time.
# This script resolves IP addresses for the 'bind_addr' and 'retry_join' properties
# of the config file at server startup time
# The ENI IDs for the cluster members are in the config file's property '_eni_ids'
# It also retypes boolean and integer property values. Somewhere in the stack build
# or cf-init process they get turned to strings.

import json
import sys
import urllib2

import boto3


def eni_to_ip(ec2, eni):
    return ec2.NetworkInterface(eni).private_ip_address


config_file = sys.argv[1]
identity = urllib2.urlopen('http://169.254.169.254/latest/dynamic/instance-identity/document').read()
region = json.loads(identity)['region']
# our eni_id is provided in this magic file, written by the userdata startup script
with open('/opt/consul/eni_id', 'r') as f:
    eni_id = f.read().strip()

ec2 = boto3.resource('ec2', region_name=region)

with open(config_file, 'r') as f:
    config = json.load(f)

config['bind_addr'] = eni_to_ip(ec2, eni_id)
config['retry_join'] = [eni_to_ip(ec2, eni) for eni in config['_eni_ids'] if eni != eni_id]
del config['_eni_ids']

# values for these keys were converted to strings by cfn-init, maybe. Convert them back.
config['bootstrap_expect'] = int(config['bootstrap_expect'])
config['server'] = (config['server'] == 'true')

with open(config_file, 'w') as f:
    json.dump(config, f)
