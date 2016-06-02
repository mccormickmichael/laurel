#!/usr/bin/python

# The CloudWatch Logs Log Stream Name is unique per cluster member.
# The cluster member number for a particular server isn't established at stack build time.
# This script resolves the server cluster index and sets the log stream name
# in the CloudWatch Logs configuration file.

import ConfigParser
import json
import sys
import urllib2

config_file = sys.argv[1]
identity = urllib2.urlopen('http://169.254.169.254/latest/dynamic/instance-identity/document').read()
region = json.loads(identity)['region']
with open('/opt/consul/cluster_index') as f:
    cluster_index = f.read().strip()

stream_name = 'consul_server_{}'.format(cluster_index)

config = ConfigParser.ConfigParser()
config.read(config_file)
config.set('consul_agent', 'log_stream_name', stream_name)

with open(config_file, 'w') as f:
    config.write(f)
