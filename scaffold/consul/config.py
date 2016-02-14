#!/usr/bin/python

# Some entries in the consul config file cannot be resolved at stack build time.
# Replace the values in those entries with values that can be resolved here.

# bind_addr: the ENI id of the instance is provided. Replace with IP address
# retry_join: the ENI ids of all other cluster members. Replace with IP addresses

import json
import sys
import boto3

config_file = sys.argv[1]
region = sys.argv[2]

ec2 = boto3.resource('ec2', region_name = region)

def ip_for(eni):
    return ec2.NetworkInterface(eni).private_ip_address

with open(config_file, 'r') as f:
    config = json.load(f)
    
config['bind_addr'] = ip_for(config['bind_addr'])
config['retry_join'] = [ ip_for(eni) for eni in config['retry_join'] ]

# values for these keys were converted to strings by cfn-init, maybe. Convert them back.
config['bootstrap_expect'] = int(config['bootstrap_expect'])
config['server'] = (config['server'] == 'true')

with open(config_file, 'w') as f:
    json.dump(config, f)
