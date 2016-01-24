#!/usr/bin/python

import argparse
import boto3

def outputs_ending(outputs, key):
    return [o['OutputValue'] for o in outputs if o['OutputKey'].endswith(key)]

def lights_out(args):
    if args.dry_run:
        echo_args(args)
        return []

    cf = boto3.resource('cloudformation', region_name = args.region)
    outputs = cf.Stack(args.stack_name).outputs
    asgs = outputs_ending(outputs, 'ASG')

    autoscale = boto3.client('autoscaling', region_name = args.region)
    for asg in asgs:
        autoscale.update_auto_scaling_group(
            AutoScalingGroupName = asg,
            MinSize = 0,
            DesiredCapacity = 0)

    return asgs

def echo_args(args):
    for k, v in vars(args).iteritems():
        print '{} : {}'.format(k, v)

def get_args():
    ap = argparse.ArgumentParser(description = 'Scale all ASGs in a stack down to zero')
    ap.add_argument('stack_name', help='Name of the stack')
    ap.add_argument('-?', '--dry-run', action = 'count', default = False, help = 'Echo parameters; take no action')
    ap.add_argument('-r', '--region', default = 'us-west-2', help = 'AWS Region in which to run')
    
    return ap.parse_args()

if __name__ == '__main__':
    args = get_args()
    results = lights_out(args)
    for asg in results:
        print 'ASG scaled to 0: {}'.format(asg)




