#!/usr/bin/python

import argparse

from stacks.vpc_nxn import NxNVPC
import stacks
from stacks.updater import Updater


def update_stack(args):

    build_parms = stacks.get_template_build_parms(args.region, args.stack_name)
    description = args.desc or stacks.get_stack_description(args.region, args.stack_name)

    echo(description, build_parms)
    
    if args.dry_run:
        return None

    template = NxNVPC(args.stack_name,
                      description=description,
                      **build_parms)
                      
    updater = Updater(args.stack_name, template.to_json(), region=args.region)
    return updater.update({})


def echo(description, build_parms):
    print 'Description: {}'.format(description)
    print 'Build Parameters:'
    for k in sorted(build_parms):
        print '  {} {}'.format(k, build_parms[k])


def get_args():
    ap = argparse.ArgumentParser(description = 'Create a VPC and Network stack with N public and N private subnets')
    ap.add_argument("stack_name", help='Name of the network stack to update')
    ap.add_argument('-r', '--region', default = 'us-west-2', help = 'AWS Region in which the stack resides')
    ap.add_argument('-d', '--desc', default = '[REPLACE ME]', help = 'Update the tack description.')
    # The parameters below are very dangerous and may not work at all if other stacks are built on this one.
    # ap.add_argument('-c', '--cidr', default = '172.16.0.0/16', help = 'Update the CIDR block of the VPC')
    # ap.add_argument('--pub-size', default = 1024, type=int, metavar = 'SIZE', help = 'Update the size of the public subnets')
    # ap.add_argument('--priv-size', default = 2048, type=int, metavar = 'SIZE', help = 'Update the size of the private subnets')
    # ap.add_argument('-azs', '--availability-zones', default = ['a', 'b', 'c'], nargs = '+', metavar = 'AZs', help = 'Change the availability zones to use')
    ap.add_argument('-?', '--dry-run', default = False, action = 'count', help = 'Echo the parameters to be used to create the stack; take no action')

    return ap.parse_args()


if __name__ == "__main__":
    args = get_args()
    results = update_stack(args)
    if results is not None:
        print 'ID:     ', results['id']
        print 'STATUS: ', results['status']
        print 'REASON: ', results['reason']

