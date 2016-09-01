#!/usr/bin/python

import argparse

import boto3

import logconfig
from arguments import add_security_control_group
from scaffold.cf import stack


def lights_on(args):
    session = boto3.session.Session(profile_name=args.profile, region_name=args.region)

    cf_client = session.client('cloudformation')
    resources = cf_client.get_template(StackName=args.stack_name)['TemplateBody']['Resources']
    asg_values = {k: {'min': v['Properties']['MinSize'],
                      'max': v['Properties']['MaxSize']}
                  for k, v in resources.items() if k.endswith('ASG')}

    outputs = stack.outputs(session, args.stack_name)

    logical_asgs = outputs.keys(lambda k: k.endswith('ASG'))
    if len(args.asg_names) > 0:
        logical_asgs = [asg for asg in logical_asgs if any((partial in asg for partial in args.asg_names))]
        asg_values = {k: asg_values[k] for k in asg_values if k in logical_asgs}

    if args.dry_run:
        print 'Not actually resetting ASG min and max values because dry run flag is set'
        return asg_values

    autoscale = session.client('autoscaling')
    for logical_asg in logical_asgs:
        autoscale.update_auto_scaling_group(
            AutoScalingGroupName=outputs[logical_asg],
            MinSize=asg_values[logical_asg]['min'],
            DesiredCapacity=asg_values[logical_asg]['min'],
            MaxSize=asg_values[logical_asg]['max'])

    return asg_values


default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='Scale all ASGs in a stack back to their stack defaults',
                                 add_help=False)
    ap.add_argument('stack_name', help='Name of the stack')
    ap.add_argument('asg_names', nargs='*',
                    help='Specific ASGs to turn off. If omitted, all ASGs in the stack will be turned off')
    add_security_control_group(ap)
    return ap.parse_args()


if __name__ == '__main__':
    logconfig.config()
    args = get_args()
    results = lights_on(args)
    # TODO: move these to logging messages
    for asg_name, values in results.iteritems():
        print 'ASG {} scaled to min: {}, max: {}'.format(asg_name, values['min'], values['max'])
