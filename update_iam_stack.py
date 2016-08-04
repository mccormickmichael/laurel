#!/usr/bin/python

import argparse

import boto3

import arguments
import logconfig
from scaffold.iam.cf_builder import IAMBuilder


def update_stack(args):
    session = boto3.session.Session(profile_name=args.profile, region_name=args.region)
    builder = IAMBuilder(args, session, True)
    return builder.build(args.dry_run)


default_desc = 'IAM Stack'
default_bucket = 'thousandleaves-iam'


def get_args():
    ap = argparse.ArgumentParser(description='Update a CloudFormation stack for logging IAM activity and API calls to an S3 bucket',
                                 add_help=False)
    req = ap.add_argument_group('Required arguments')
    req.add_argument("stack_name",
                     help='Name of the iam stack to update')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc', default=default_desc,
                    help=arguments.generate_help('Stack description.', default_desc))
    st.add_argument('--bucket', default=default_bucket,
                    help=arguments.generate_help('Bucket name', default_bucket))
    st.add_argument('--enable', type=bool, default=False,
                    help='Enable API logging. Defaults to False')

    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)

    return ap.parse_args()


if __name__ == "__main__":
    logconfig.config()
    args = get_args()
    results = update_stack(args)
    if results.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack.stack_id
        print 'STATUS: ', results.stack.stack_status
        if results.stack.stack_status_reason is not None:
            print 'REASON: ', results.stack.stack_status_reason
