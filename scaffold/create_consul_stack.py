#!/usr/bin/python

import argparse
import glob

import boto3

import stacks
from stacks.consul import ConsulTemplate
from stacks import Outputs
from stacks.creator import Creator
from stacks.updater import Updater

def create_stack(args):

    cf = boto3.resource('cloudformation', region_name = args.region)
    outputs = Outputs(cf.Stack(args.network_stack_name))

    vpc_id = outputs['VpcId']
    vpc_cidr = outputs['VpcCidr']
    subnet_ids = outputs.values(lambda k: 'PrivateSubnet' in k)

    echo_args({
        'Stack Name   ' : args.stack_name,
        'Region       ' : args.region,
        'Bucket       ' : args.bucket,
        'Description  ' : args.desc,
        'VPC ID       ' : vpc_id,
        'VPC CIDR     ' : vpc_cidr,
        'Subnets      ' : subnet_ids,
        'Cluster Size ' : args.cluster_size,
        'Update       ' : args.update
    })

    s3 = boto3.resource('s3', region_name = args.region)
    bucket = s3.Bucket(args.bucket)
    prefix = 'scaffold/'
    for fname in glob.glob('consul/*'):
        print fname
        with open(fname, 'r') as f:
            bucket.put_object(Key = prefix + fname,
                              Body = f.read())

    if args.dry_run:
        return

    template = ConsulTemplate(args.stack_name,
                              region = args.region,
                              bucket = args.bucket,
                              description = args.desc,
                              vpc_id = vpc_id,
                              vpc_cidr = vpc_cidr,
                              subnet_ids = subnet_ids,
                              cluster_size = args.cluster_size)

    stack_parms = {
        ConsulTemplate.CONSUL_KEY_PARAM_NAME : args.key
    }

    if args.update:
        updater = Updater(args.stack_name, template.to_json(), region = args.region, bucket_name = args.bucket)
        return updater.update(stack_parms)

    creator = Creator(args.stack_name, template.to_json(), region = args.region, bucket_name = args.bucket)
    return creator.create(stack_parms)

def echo_args(args):
    for k, v in args.iteritems():
        print '{} : {}'.format(k, v)

def get_args():
    ap = argparse.ArgumentParser(description = 'Create a stack that provisions a Consul cluster')
    ap.add_argument('stack_name', help='Name of the Consul stack')
    ap.add_argument('network_stack_name', help='Name of the network stack')
    ap.add_argument('-?', '--dry-run', action = 'count', default = False, help = 'Take no action')
    ap.add_argument('-d', '--desc', default = '[REPLACE ME]', help = 'Stack description. Strongy encouraged')
    ap.add_argument('-c', '--cluster-size', default = 3, type = int, help = 'Number of instances in the cluster')
    ap.add_argument('-r', '--region', default = 'us-west-2', help = 'AWS Region in which to create the stack')
    ap.add_argument('-b', '--bucket', default = 'thousandleaves-us-west-2-laurel-deploy', help = 'S3 bucket to use for the stack template and resources')
    ap.add_argument('-k', '--key', required = True, help = 'Name of the key pair to access the consul servers. Required.')
    ap.add_argument('-u', '--update', action = 'store_true', help = 'Update the stack')
    
    return ap.parse_args()

if __name__ == '__main__':
    args = get_args()
    results = create_stack(args)
    if results is not None:
        print 'ID:     ', results['id']
        print 'STATUS: ', results['status']
        print 'REASON: ', results['reason']

