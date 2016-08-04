#!/usr/bin/python

import argparse

import boto3

import arguments
import logconfig
from scaffold.consul.consul_builder import ConsulBuilder


def update_stack(args):
    session = boto3.session.Session(profile_name=args.profile)
    builder = ConsulBuilder(args, session, True)
    return builder.build(args.dry_run)


def get_args():
    ap = argparse.ArgumentParser(description='Create a CloudFormation stack hosting a Consul cluster',
                                 add_help=False)
    req = ap.add_argument_group('Required')
    req.add_argument('stack_name',
                     help='Name of the Consul stack to create')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc',
                    help='Stack description.')
    st.add_argument('--consul-key',
                    help='Name of the key pair used to access the Consul cluster instances.')
    st.add_argument('--instance-type',
                    help='Instance type for the Consul servers.')
    st.add_argument('--ui-instance-type',
                    help='Instance type for the Consul UI servers.')
    st.add_argument('--cluster_size',
                    help='Number of instances in the Consul cluster. Should be an odd number > 1.')
    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)
    return ap.parse_args()

if __name__ == '__main__':
    logconfig.config()
    args = get_args()
    results = update_stack(args)
    # TODO: move these to logging messages
    if results.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack.stack_id
        print 'STATUS: ', results.stack.stack_status
        if results.stack.stack_status_reason is not None:
            print 'REASON: ', results.stack.stack_status_reason
