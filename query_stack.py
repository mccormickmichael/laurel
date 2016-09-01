# Query a CloudFormation stack.
# Returns:
# - Build Parameters - the parameters sent to the TemplateBuilder when generating the template
# - Stack Parameters - the parameters sent to CF during stack create or update time.

import argparse

import arguments
import logconfig
import session
from scaffold.cf import stack


def query_stack(stack_name, profile):
    boto3_session = session.new(args.profile, args.region, args.role)

    return [
        stack.summary(boto3_session, stack_name).build_parameters(),
        stack.parameters(boto3_session, stack_name)
    ]


default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='Query a CloudFormation stack for build and template parameters',
                                 add_help=False)
    ap.add_argument('stack_name',
                    help='Name of the stack to query')
    arguments.add_security_control_group(ap)
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
