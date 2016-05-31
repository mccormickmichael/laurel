#!/usr/bin/python

# Some entries in the consul config file cannot be resolved at stack build time.
# Replace the values in those entries with values that can be resolved here.

# bind_addr: the ENI id of the instance is provided. Replace with IP address
# retry_join: the ENI ids of all other cluster members. Replace with IP addresses

import json
import sys
import urllib2

import boto3


def eni_to_ip(ec2, eni):
    return ec2.NetworkInterface(eni).private_ip_address


identity = urllib2.urlopen('http://169.254.169.254/latest/dynamic/instance-identity/document').read()
region = json.loads(identity)['region']

config_file = sys.argv[1]

ec2 = boto3.resource('ec2', region_name=region)

with open(config_file, 'r') as f:
    config = json.load(f)

config['bind_addr'] = eni_to_ip(ec2, config['bind_addr'])
config['retry_join'] = [eni_to_ip(ec2, eni) for eni in config['retry_join']]

# values for these keys were converted to strings by cfn-init, maybe. Convert them back.
config['bootstrap_expect'] = int(config['bootstrap_expect'])
config['server'] = (config['server'] == 'true')

with open(config_file, 'w') as f:
    json.dump(config, f)
