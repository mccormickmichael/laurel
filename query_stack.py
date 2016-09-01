# Query a CloudFormation stack.
# Returns:
# - Build Parameters - the parameters sent to the TemplateBuilder when generating the template
# - Stack Parameters - the parameters sent to CF during stack create or update time.

import argparse

import boto3

import logconfig
from scaffold.cf import stack


def query_stack(stack_name, profile):
    session = boto3.session.Session(profile_name=profile)

    return [
        stack.summary(session, stack_name).build_parameters(),
        stack.parameters(session, stack_name)
    ]


default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='Query a CloudFormation stack for build and template parameters')
    ap.add_argument('stack_name',
                    help='Name of the stack to query')
    ap.add_argument('--profile', default=default_profile,
                    help='AWS Credential and Config profile to use. Default: {}'.format(default_profile))
    return ap.parse_args()

if __name__ == '__main__':
    logconfig.config()
    args = get_args()
    build_parms, stack_parms = query_stack(args.stack_name, args.profile)
    # TODO: move these to logging messages
    print('Build Parameters:')
    if len(build_parms) == 0:
        print('  (none)')
    else:
        for name, value in build_parms.items():
            print('  {} : {}'.format(name, value))
    print('Stack Parameters:')
    if len(stack_parms) == 0:
        print('  (none)')
    else:
        for name, value in stack_parms.items():
            print('  {} : {}'.format(name, value))
