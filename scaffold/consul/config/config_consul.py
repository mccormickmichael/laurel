#!/usr/bin/python

# The IP addressses of consul cluster members are not known at stack build time.
# This script resolves IP addresses for the 'retry_join' property of the config file at server startup time
# The ENI IDs for the cluster members are in the config file's property '_eni_ids'
# Also resolves the 'bind_addr' IP address for server members
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

ec2 = boto3.resource('ec2', region_name=region)

with open(config_file, 'r') as f:
    config = json.load(f)

eni_id = 'bogus'

if 'server' in config:  # server mode
    # our eni_id is provided in this magic file, written by the userdata startup script
    with open('/opt/consul/eni_id', 'r') as f:
        eni_id = f.read().strip()
    config['bind_addr'] = eni_to_ip(ec2, eni_id)
    config['bootstrap_expect'] = int(config['bootstrap_expect'])
    config['server'] = True
elif 'ui' in config:  # web UI mode
    config['ui'] = True
else:  # generic client agent mode
    pass

config['retry_join'] = [eni_to_ip(ec2, eni) for eni in config['_eni_ids'] if eni != eni_id]
del config['_eni_ids']

with open(config_file, 'w') as f:
    json.dump(config, f)
