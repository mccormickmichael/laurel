#!/usr/bin/python

import argparse

import boto3

from scaffold.stack import Outputs


def lights_on(args):
    session = boto3.session.Session(profile_name=args.profile)

    cf = session.resource('cloudformation')
    cf_client = cf.meta.client
    resources = cf_client.get_template(StackName=args.stack_name)['TemplateBody']['Resources']
    asg_values = {k: {'min': v['Properties']['MinSize'],
                      'max': v['Properties']['MaxSize']}
                  for k, v in resources.items() if k.endswith('ASG')}

    outputs = Outputs(cf.Stack(args.stack_name))

    if args.dry_run:
        print 'Not actually resetting ASG min and max values because dry run flag is set'
        return asg_values

    autoscale = session.client('autoscaling')
    for logical_asg in outputs.keys(lambda k: k.endswith('ASG')):
        autoscale.update_auto_scaling_group(
            AutoScalingGroupName=outputs[logical_asg],
            MinSize=asg_values[logical_asg]['min'],
            DesiredCapacity=asg_values[logical_asg]['min'],
            MaxSize=asg_values[logical_asg]['max'])

    return asg_values


default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='Scale all ASGs in a stack back to their stack defaults')
    ap.add_argument('stack_name', help='Name of the stack')

    ap.add_argument('--profile', default=default_profile,
                    help='AWS Credential and Config profile to use. Default: {}'.format(default_profile))
    ap.add_argument('--dry-run', action='store_true', default=False,
                    help='Echo the parameters to be used to create the stack; take no action')
    return ap.parse_args()


if __name__ == '__main__':
    args = get_args()
    results = lights_on(args)
    for asg_name, values in results.iteritems():
        print 'ASG {} scaled to min: {}, max: {}'.format(asg_name, values['min'], values['max'])
