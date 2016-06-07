#!/usr/bin/python

import argparse

import boto3

import arguments
from scaffold.consul.consul_builder import ConsulBuilder


def create_stack(args):
    session = boto3.session.Session(profile_name=args.profile)
    builder = ConsulBuilder(args, session, False)
    return builder.build(args.dry_run)


default_desc = 'Consul Stack'
default_instance_type = 't2.micro'
default_ui_instance_type = 't2.micro'
default_cluster_size = 3


def get_args():
    ap = argparse.ArgumentParser(description='Create a CloudFormation stack hosting a Consul cluster',
                                 add_help=False)
    req = ap.add_argument_group('Required')
    ap.add_argument('stack_name',
                    help='Name of the Consul stack to create')
    req.add_argument('network_stack_name',
                     help='Name of the network stack')
    req.add_argument('--consul-key', required=True,
                     help='Name of the key pair used to access the Consul cluster instances.')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc', default=default_desc,
                    help=arguments.generate_help('Stack description.', default_desc))
    st.add_argument('--instance-type', default=default_instance_type,
                    help=arguments.generate_help('Instance type for the Consul servers.', default_instance_type))
    st.add_argument('--ui-instance-type', default=default_ui_instance_type,
                    help=arguments.generate_help('Instance type for the Consul UI servers.', default_ui_instance_type))
    st.add_argument('--cluster_size', default=default_cluster_size,
                    help=arguments.generate_help('Number of instances in the Consul cluster. Should be an odd number > 1.', default_cluster_size))
    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)
    return ap.parse_args()


if __name__ == '__main__':
    args = get_args()
    results = create_stack(args)
    if results.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack.stack_id
        print 'STATUS: ', results.stack.stack_status
        if results.stack.stack_status_reason is not None:
            print 'REASON: ', results.stack.stack_status_reason
