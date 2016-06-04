#!/usr/bin/python

import argparse

import boto3

from scaffold import stack


def matches_any(name, partial_names):
    return any((partial in name for partial in partial_names))


def lights_out(args):
    session = boto3.session.Session(profile_name=args.profile)

    outputs = stack.outputs(session, args.stack_name)
    logical_asgs = outputs.keys(lambda k: k.endswith('ASG'))
    if len(args.asg_names) > 0:
        logical_asgs = [asg for asg in logical_asgs if any((partial in asg for partial in args.asg_names))]

    physical_asgs = [outputs[asg] for asg in logical_asgs]

    if args.dry_run:
        print 'Not actually scaling ASGs to zero because dry-run flag is set.'
        return physical_asgs

    autoscale = session.client('autoscaling')
    for asg in physical_asgs:
        autoscale.update_auto_scaling_group(
            AutoScalingGroupName=asg,
            MinSize=0,
            DesiredCapacity=0,
            MaxSize=0)

    return physical_asgs


default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='Turn out the lights. Scale ASGs in a stack down to zero.')
    ap.add_argument('stack_name', help='Name of the stack')
    ap.add_argument('asg_names', nargs='*',
                    help='Specific ASGs to turn off. If omitted, all ASGs in the stack will be turned off')

    ap.add_argument('--profile', default=default_profile,
                    help='AWS Credential and Config profile to use. Default: {}'.format(default_profile))
    ap.add_argument('--dry-run', action='store_true', default=False,
                    help='Echo the parameters to be used to create the stack; take no action')
    return ap.parse_args()


if __name__ == '__main__':
    args = get_args()
    results = lights_out(args)
    for asg in results:
        print 'ASG scaled to 0: {}'.format(asg)
