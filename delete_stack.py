#!/usr/bin/python
# Delete a stack

import argparse

import arguments
import logconfig
import session
from scaffold.cf.stack.operation import StackDeleter


def delete_stack(args):
    boto3_session = session.new(args.profile, args.region, args.role)

    deleter = StackDeleter(boto3_session, args.stack_name)
    if args.dry_run:
        deleter.validate_stack_exists()
        return 'Stack {} exists'.format(args.stack_name)

    deleter.validate_stack_exists()
    deleter.delete()
    return 'Stack {} deleted'.format(args.stack_name)


default_profile = 'default'
default_region = 'us-west-2'


def get_args():
    ap = argparse.ArgumentParser(description='Delete a CloudFormation stack', add_help=False)
    ap.add_argument('stack_name',
                    help='Name of the stack to delete')
    arguments.add_security_control_group(ap)
    return ap.parse_args()


if __name__ == '__main__':
    logconfig.config()
    args = get_args()
    results = delete_stack(args)
    # TODO: move these to logging messages
    print results
