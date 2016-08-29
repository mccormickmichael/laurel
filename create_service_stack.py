#!/usr/bin/python

import argparse

import boto3

import arguments
import logconfig
from scaffold.services.services_builder import ServicesBuilder


def create_stack(args):
    session = boto3.session.Session(profile_name=args.profile, region_name=args.region)
    builder = ServicesBuilder(args, session, False)
    return builder.build(args.dry_run)


default_desc = 'Services Stack'
default_bastion_type = 't2.micro'
default_nat_type = 't2.micro'


def get_args():
    ap = argparse.ArgumentParser(description='Create a stack containing a NAT and Bastion server',
                                 add_help=False)
    req = ap.add_argument_group('Required')
    req.add_argument('stack_name',
                     help='Name of the services stack to create')
    req.add_argument('network_stack_name',
                     help='Name of the network stack')
    req.add_argument('--bastion-key', required=True,
                     help='Name of the key pair to access the bastion server.')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc', default=default_desc,
                    help=arguments.generate_help('Stack description.', default_desc))
    st.add_argument('--bastion-type', default=default_bastion_type,
                    help=arguments.generate_help('Instance type of the Bastion server.', default_bastion_type))
    st.add_argument('--nat-type', default=default_nat_type,
                    help=arguments.generate_help('Instance type of the NAT server.', default_nat_type))

    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)

    return ap.parse_args()


if __name__ == '__main__':
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
