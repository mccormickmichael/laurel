#!/usr/bin/python

import argparse

import boto3

from stacks.services import ServicesTemplate
from stacks import Outputs
from stacks.creator import Creator
from stacks.updater import Updater
import stacks


def create_stack(args):
    if args.dry_run:
        echo_args(args)
        return None

    cf = boto3.resource('cloudformation', region_name = args.region)
    outputs = Outputs(cf.Stack(args.network_stack_name))

    vpc_id = outputs['VpcId']
    vpc_cidr = outputs['VpcCidr']
    priv_rt_id = outputs['PrivateRT']
    pub_subnet_ids = outputs.values(lambda k: 'PublicSubnet' in k)

    template = ServicesTemplate(args.stack_name,
                                description = args.desc,
                                vpc_id = vpc_id,
                                vpc_cidr = vpc_cidr,
                                private_route_table_id = priv_rt_id,
                                public_subnet_ids = pub_subnet_ids)

    stack_parms = {
        ServicesTemplate.BASTION_KEY_PARM_NAME : args.key
    }

    if args.update:
        updater = Updater(args.stack_name, template.to_json(), region = args.region)
        return updater.update(stack_parms)

    creator = Creator(args.stack_name, template.to_json(), region = args.region)
    return creator.create(stack_parms)

def echo_args(args):
    for k, v in vars(args).iteritems():
        print '{} : {}'.format(k, v)

def get_args():
    ap = argparse.ArgumentParser(description = 'Create a stack containing a NAT and Bastion server')
    ap.add_argument('stack_name', help='Name of the stack to create')
    ap.add_argument('network_stack_name', help='Name of the network stack')
    ap.add_argument('-?', '--dry-run', action = 'count', default = False, help = 'Echo the parameters to be used to create the stack; take no action')
    ap.add_argument('-d', '--desc', default = '[REPLACE ME]', help = 'Stack description. Strongy encouraged.')
    ap.add_argument('-r', '--region', default = 'us-west-2', help = 'AWS Region in which to create the stack')
    ap.add_argument('-k', '--key', required = True, help = 'Name of the key pair to access the bastion server. Required.')
    ap.add_argument('-u', '--update', action = 'store_true', help = 'Update the stack')
    
    return ap.parse_args()

if __name__ == '__main__':
    args = get_args()
    results = create_stack(args)
    if results is not None:
        print 'ID:     ', results['id']
        print 'STATUS: ', results['status']
        print 'REASON: ', results['reason']

