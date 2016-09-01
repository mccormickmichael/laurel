#!/usr/bin/python

import argparse


import arguments
import logconfig
import session
from scaffold.iam.cf_builder import IAMBuilder


def create_stack(args):
    boto3_session = session.new(args.profile, args.region, args.role)
    builder = IAMBuilder(args, boto3_session, False)
    return builder.build(args.dry_run)


default_desc = 'IAM Stack'
default_bucket = 'thousandleaves-iam'


def get_args():
    ap = argparse.ArgumentParser(description='Create a CloudFormation stack for logging IAM activity and API calls to an S3 bucket',
                                 add_help=False)
    req = ap.add_argument_group('Required arguments')
    req.add_argument("stack_name",
                     help='Name of the iam stack to create')

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
    results = create_stack(args)
    # TODO: move these to logging messages
    if results.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack.stack_id
        print 'STATUS: ', results.stack.stack_status
        if results.stack.stack_status_reason is not None:
            print 'REASON: ', results.stack.stack_status_reason
