#!/usr/bin/python

import argparse

import boto3
from template.consul import ConsulTemplate
import stacks
import stacks.outputs as so

def create_stack(args):

    cf = boto3.resource('cloudformation', region_name = args.region)
    outputs = cf.Stack(args.network_stack_name).outputs

    vpc_id = so.value(outputs, 'VpcId')
    vpc_cidr = so.value(outputs, 'VpcCidr')
    subnet_ids = so.values(outputs, lambda k: 'PrivateSubnet' in k)

    echo_args({
        'Stack Name   ' : args.stack_name,
        'Description  ' : args.desc,
        'VPC ID       ' : vpc_id,
        'VPC CIDR     ' : vpc_cidr,
        'Subnets      ' : subnet_ids,
        'Cluster Size ' : args.cluster_size})

    if args.dry_run:
        return

    template = ConsulTemplate(args.stack_name,
                              description = args.desc,
                              vpc_id = vpc_id,
                              vpc_cidr = vpc_cidr,
                              subnet_ids = subnet_ids,
                              cluster_size = args.cluster_size)

    stack_parms = {
        ConsulTemplate.CONSUL_KEY_PARAM_NAME : args.key
    }

    creator = stacks.Creator(args.stack_name, template.to_json(), region = args.region)
    results = creator.create(stack_parms)

def echo_args(args):
    for k, v in args.iteritems():
        print '{} : {}'.format(k, v)

def get_args():
    ap = argparse.ArgumentParser(description = 'Create a stack that provisions a Consul cluster')
    ap.add_argument('stack_name', help='Name of the Consul stack')
    ap.add_argument('network_stack_name', help='Name of the network stack')
    ap.add_argument('-?', '--dry-run', action = 'count', default = False, help = 'Take no action')
    ap.add_argument('-d', '--desc', default = '[REPLACE ME]', help = 'Stack description. Strongy encouraged')
    ap.add_argument('-c', '--cluster-size', default = 3, help = 'Number of instances in the cluster')
    ap.add_argument('-r', '--region', default = 'us-west-2', help = 'AWS Region in which to create the stack')
    ap.add_argument('-k', '--key', required = True, help = 'Name of the key pair to access the consul servers. Required.')
    
    return ap.parse_args()

if __name__ == '__main__':
    args = get_args()
    results = create_stack(args)
    if results is not None:
        print 'ID:     ', results['id']
        print 'STATUS: ', results['status']
        print 'REASON: ', results['reason']

