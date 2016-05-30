# Query a CloudFormation stack.
# Returns:
# - Build Parameters - the parameters sent to the TemplateBuilder when generating the template
# - Stack Parameters - the parameters sent to CF during stack create or update time.

import argparse

import boto3

from scaffold.stack.operation import StackQuery


def query_stack(stack_name, profile):
    session = boto3.session.Session(profile_name=profile)
    query = StackQuery(session, stack_name)
    return (query.get_build_parameters(), query.get_stack_parameters())


default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='Query a CloudFormation stack for build and template parameters')
    ap.add_argument('stack_name',
                    help='Name of the stack to query')
    ap.add_argument('--profile', default=default_profile,
                    help='AWS Credential and Config profile to use. Default: {}'.format(default_profile))
    return ap.parse_args()

if __name__ == '__main__':
    args = get_args()
    build_parms, stack_parms = query_stack(args.stack_name, args.profile)
    print('Build Parameters:')
    if len(build_parms) == 0:
        print('  (none)')
    else:
        for name, value in build_parms.iteritems():
            print('  {} : {}'.format(name, value))
    print('Stack Parameters:')
    if len(stack_parms) == 0:
        print('  (none)')
    else:
        for name, value in stack_parms.iteritems():
            print('  {} : {}'.format(name, value))
