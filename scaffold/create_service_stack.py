#!/usr/bin/python

import argparse
from template.services import ServicesTemplate
import stacks.outputs as so
import boto3
import stack

def output_matching(outputs, key):
    return [o['OutputValue'] for o in outputs if o['OutputKey'] == key][0]

def outputs_containing(outputs, key_fragment):
    return [o['OutputValue'] for o in outputs if key_fragment in o['OutputKey']]

def create_stack(args):
    if args.dry_run:
        echo_args(args)
        return None

    cf = boto3.resource('cloudformation', region_name = args.region)
    outputs = cf.Stack(args.network_stack_name).outputs

    vpc_id = so.value(outputs, 'VpcId')
    vpc_cidr = so.value(outputs, 'VpcCidr')
    priv_rt_id = so.value(outputs, 'PrivateRT')
    pub_subnet_ids = so.values(outputs, lambda k: 'PublicSubnet' in k)

    template = ServicesTemplate(args.stack_name,
                                description = args.desc,
                                vpc_id = vpc_id,
                                vpc_cidr = vpc_cidr,
                                private_route_table_id = priv_rt_id,
                                public_subnet_ids = pub_subnet_ids)

    stack_parms = {
        ServicesTemplate.BASTION_KEY_PARM_NAME : args.key
    }

    creator = stack.Creator(args.stack_name, template.to_json(), region = args.region)
    results = creator.create(stack_parms)

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
    
    return ap.parse_args()

if __name__ == '__main__':
    args = get_args()
    results = create_stack(args)
    if results is not None:
        print 'ID:     ', results['id']
        print 'STATUS: ', results['status']
        print 'REASON: ', results['reason']

