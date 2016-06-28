#!/usr/bin/python

import argparse

import boto3

import arguments
from scaffold.iam.cf_builder import IAMBuilder


def create_stack(args):
    session = boto3.session.Session(profile_name=args.profile)
    builder = IAMBuilder(args, session, False)
    return builder.build(args.dry_run)


default_desc = 'IAM Stack'


def get_args():
    ap = argparse.ArgumentParser(description='Create a CloudFormation stack with global IAM roles and policies',
                                 add_help=False)
    req = ap.add_argument_group('Required arguments')
    req.add_argument("stack_name",
                     help='Name of the network stack to create')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc', default=default_desc,
                    help=arguments.generate_help('Stack description.', default_desc))
    st.add_argument('--base-dir', default=None,
                    help='Base directory for role and policy documents')

    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)

    return ap.parse_args()


if __name__ == "__main__":
    args = get_args()
    results = create_stack(args)
    if results.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack.stack_id
        print 'STATUS: ', results.stack.stack_status
        if results.stack.stack_status_reason is not None:
            print 'REASON: ', results.stack.stack_status_reason
