#!/usr/bin/python
# Delete a stack

import argparse

import boto3

import logconfig
from arguments import add_security_control_group
from scaffold.cf.stack.operation import StackDeleter


def delete_stack(args):
    session = boto3.session.Session(profile_name=args.profile, region_name=args.region)

    deleter = StackDeleter(session, args.stack_name)
    if args.dry_run:
        deleter.validate_stack_exists()
        return 'Stack {} exists'.format(args.stack_name)

    deleter.delete()
    return 'Stack {} deleted'.format(args.stack_name)


default_profile = 'default'
default_region = 'us-west-2'


def get_args():
    ap = argparse.ArgumentParser(description='Delete a CloudFormation stack', add_help=False)
    ap.add_argument('stack_name',
                    help='Name of the stack to delete')
    add_security_control_group(ap)
    return ap.parse_args()


if __name__ == '__main__':
    logconfig.config()
    args = get_args()
    results = delete_stack(args)
    # TODO: move these to logging messages
    print results
