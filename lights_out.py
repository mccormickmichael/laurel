#!/usr/bin/python

import argparse

import boto3

from scaffold.stack import Outputs


def lights_out(args):
    session = boto3.session.Session(profile_name=args.profile)

    cf = session.resource('cloudformation')

    outputs = Outputs(cf.Stack(args.stack_name))
    asgs = outputs.values(lambda k: k.endswith('ASG'))

    if args.dry_run:
        print 'Not actually scaling ASGs to zero because dry-run flag is set.'
        return asgs

    autoscale = session.client('autoscaling')
    for asg in asgs:
        autoscale.update_auto_scaling_group(
            AutoScalingGroupName=asg,
            MinSize=0,
            DesiredCapacity=0,
            MaxSize=0)

    return asgs


default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='Turn out the lights. Scale all ASGs in a stack down to zero.')
    ap.add_argument('stack_name', help='Name of the stack')

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
