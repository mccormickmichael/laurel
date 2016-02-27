#!/usr/bin/python

import argparse

from network.vpc_nxn import NxNVPC
from stack.creator import Creator

def create_stack(args):
    if args.dry_run:
        echo_args(args)
        return None
    
    template = NxNVPC(args.stack_name,
                      description = args.desc,
                      vpc_cidr = args.cidr,
                      region = args.region,
                      availability_zones = args.availability_zones,
                      pub_size = args.pub_size,
                      priv_size = args.priv_size)
                      
    creator = Creator(args.stack_name, template.to_json(), region = args.region)
    return creator.create({})

def echo_args(args):
    for k, v in vars(args).iteritems():
        print '{} : {}'.format(k, v)

def get_args():
    ap = argparse.ArgumentParser(description = 'Create a VPC and Network stack with N public and N private subnets')
    ap.add_argument("stack_name", help='Name of the network stack to create')
    ap.add_argument('-?', '--dry-run', default = False, action = 'count', help = 'Echo the parameters to be used to create the stack; take no action')
    ap.add_argument('-d', '--desc', default = '[REPLACE ME]', help = 'Stack description. Strongy encouraged.')
    ap.add_argument('-r', '--region', default = 'us-west-2', help = 'AWS Region in which to create the stack')
    ap.add_argument('-c', '--cidr', default = '172.16.0.0/16', help = 'CIDR block of the VPC')
    ap.add_argument('--pub-size', default = 1024, type=int, metavar = 'SIZE', help = 'Size of the public subnets')
    ap.add_argument('--priv-size', default = 2048, type=int, metavar = 'SIZE', help = 'Size of the private subnets')
    ap.add_argument('-azs', '--availability-zones', default = ['a', 'b', 'c'], nargs = '+', metavar = 'AZs', help = 'List of availability zones to use')

    return ap.parse_args()


if __name__ == "__main__":
    args = get_args()
    results = create_stack(args)
    if results is not None:
        print 'ID:     ', results['id']
        print 'STATUS: ', results['status']
        print 'REASON: ', results['reason']
