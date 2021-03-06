#!/usr/bin/python

import argparse

import arguments
import logconfig
import session
from scaffold.stile.stile_builder import StileBuilder


def update_stack(args):
    boto3_session = session.new(args.profile, args.region, args.role)
    builder = StileBuilder(args, boto3_session, True)
    return builder.build(args.dry_run)


def get_args():
    ap = argparse.ArgumentParser(description='''Update a CloudFormation stack created with 'create_service_stack'.''',
                                 add_help=False)
    req = ap.add_argument_group('Required')
    req.add_argument("stack_name",
                     help='Name of the stack to update')
    req.add_argument('--bastion-key', required=True,
                     help='Name of the key pair to access the bastion server.')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc',
                    help='Stack description.')
    st.add_argument('--bastion-type',
                    help='Instance type of the Bastion server.')
    st.add_argument('--nat-type',
                    help='Instance type of the NAT server.')

    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)
    return ap.parse_args()


if __name__ == "__main__":
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
