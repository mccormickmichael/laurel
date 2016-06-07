#!/usr/bin/python

import argparse
from datetime import datetime

import boto3

import arguments
from scaffold.network.vpc_template import VpcTemplate
from scaffold.stack.operation import StackOperation
from scaffold.doby import Doby


def create_stack(args):
    key_prefix = '{}/vpc_nxn-{}'.format(args.s3_key_prefix, datetime.utcnow().strftime('%Y%m%d-%H%M%S'))
    session = boto3.session.Session(profile_name=args.profile)

    template = VpcTemplate(args.stack_name,
                           region=session.region_name,
                           description=args.desc,
                           vpc_cidr=args.cidr,
                           availability_zones=args.availability_zones,
                           pub_size=args.pub_size,
                           priv_size=args.priv_size)
    template.build_template()
    template_json = template.to_json()

    results = {'template': template_json}

    if args.dry_run:
        return Doby(results)

    creator = StackOperation(session, args.stack_name, template_json, args.s3_bucket, key_prefix)
    stack = creator.create()
    results['stack_id'] = stack.stack_id
    results['stack_status'] = stack.stack_status
    results['stack_status_reason'] = stack.stack_status_reason
    # the return values here suck. How can we do better?
    return Doby(results)


default_desc = 'Network Stack'
default_cidr = '172.16.0.0/18'
default_azs = ['a', 'b', 'c']
default_pub_size = 1024
default_priv_size = 2048


def get_args():
    ap = argparse.ArgumentParser(description='Create a VPC CloudFormation stack with N public and private subnets',
                                 add_help=False)
    req = ap.add_argument_group('Required arguments')
    req.add_argument("stack_name",
                     help='Name of the network stack to create')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc', default=default_desc,
                    help=arguments.generate_help('Stack description.', default_desc))
    st.add_argument('--cidr', default=default_cidr,
                    help=arguments.generate_help('CIDR block of the VPC.', default_cidr))
    st.add_argument('--availability-zones', default=default_azs, nargs='+', metavar='AZ',
                    help=arguments.generate_help('Space-separated list of availability zones to use. Will determine the number of subnets.', default_azs))
    st.add_argument('--pub-size', default=default_pub_size, type=int, metavar='SIZE',
                    help=arguments.generate_help('Size of the public subnets.', default_pub_size))
    st.add_argument('--priv-size', default=default_priv_size, type=int, metavar='SIZE',
                    help=arguments.generate_help('Size of the private subnets.', default_priv_size))

    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)

    return ap.parse_args()


if __name__ == "__main__":
    args = get_args()
    results = create_stack(args)
    if args.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack_id
        print 'STATUS: ', results.stack_status
        if results.stack_status_reason is not None:
            print 'REASON: ', results.stack_status_reason
