#!/usr/bin/python
# Delete a stack

import argparse

import boto3

from scaffold.stack.operation import StackDeleter


def delete_stack(args):
    session = boto3.session.Session(profile_name=args.profile)

    deleter = StackDeleter(session, args.stack_name)
    if args.dry_run:
        deleter.validate_stack_exists()
        return 'Stack {} exists'.format(args.stack_name)

    deleter.delete()
    return 'Stack {} deleted'.format(args.stack_name)


default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='Delete a CloudFormation stack')
    ap.add_argument('stack_name',
                    help='Name of the stack to delete')

    ap.add_argument('--profile', default=default_profile,
                    help='AWS Credential and Config profile to use. Default: {}'.format(default_profile))
    ap.add_argument('--dry-run', action='store_true', default=False,
                    help='Validate permissions and parameters. Take no action.')
    return ap.parse_args()


if __name__ == '__main__':
    args = get_args()
    results = delete_stack(args)
    print results
