#!/usr/bin/python

import argparse
from datetime import datetime

import boto3

import arguments
from scaffold.network.vpc_creator import VpcCreator


def update_stack(args):
    session = boto3.session.Session(profile_name=args.profile)
    builder = VpcCreator(args, session, True)
    return builder.create(args.dry_run)


def get_args():
    ap = argparse.ArgumentParser(description='''Update a CloudFormation stack created with 'create_vpc'.''',
                                 add_help=False)
    req = ap.add_argument_group('Required arguments')
    req.add_argument("stack_name",
                     help='Name of the network stack to update')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc',
                    help='Stack description. Strongy encouraged.')
    st.add_argument('--cidr',
                    help='CIDR block of the VPC.')
    st.add_argument('--availability-zones', nargs='+', metavar='AZ',
                    help='Space-separated list of availability zones to use. Will determine the number of subnets.')
    st.add_argument('--pub-size', type=int, metavar='SIZE',
                    help='Size of the public subnets.')
    st.add_argument('--priv-size', type=int, metavar='SIZE',
                    help='Size of the private subnets.')

    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)

    return ap.parse_args()


if __name__ == "__main__":
    args = get_args()
    results = update_stack(args)
    if args.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack_id
        print 'STATUS: ', results.stack_status
        if results.stack_status_reason is not None:
            print 'REASON: ', results.stack_status_reason
