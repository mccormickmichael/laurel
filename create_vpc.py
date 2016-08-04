#!/usr/bin/python

import argparse

import boto3

import arguments
import logconfig
from scaffold.network.vpc_builder import VpcBuilder


def create_stack(args):
    session = boto3.session.Session(profile_name=args.profile)
    builder = VpcBuilder(args, session, False)
    return builder.build(args.dry_run)


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
    logconfig.config()
    args = get_args()
    results = create_stack(args)
    # TODO: move these to logging messages
    if results.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack.stack_id
        print 'STATUS: ', results.stack.stack_status
        if results.stack.stack_status_reason is not None:
            print 'REASON: ', results.stack.stack_status_reason
