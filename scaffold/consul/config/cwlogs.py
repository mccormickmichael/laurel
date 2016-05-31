#!/usr/bin/python

# Resolve LogStream and LogGroup entries in the CloudWatch Logs configuration file

import ConfigParser
import json
import sys
import urllib2

import boto3

config_file = sys.argv[1]
index = sys.argv[2]
with (urllib2.urlopen('http://169.254.169.254/latest/dynamic/instance-identity/document')) as f:
    region = json.load(f)['region']

cf = boto3.resource('cloudformation', region_name=region)
consul_stack = cf.Stack('CapConsul')  # TODO: parameterize this

group_name = next((o.OutputValue for o in consul_stack.outputs if o.OutputKey == 'ConsulLogGroup'))
stream_name = 'consul_server_{}'.format(index)

config = ConfigParser.ConfigParser()
config.read(config_file)
config.set('/var/log/consul', 'log_group_name', group_name)
config.set('/var/log/consul', 'log_stream_name', stream_name)

config.write(sys.stdout)
