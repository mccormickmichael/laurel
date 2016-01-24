#!/usr/bin/python

import argparse
import boto3
import json
import inspect

def output_dict_ending(outputs, key):
    return {o['OutputKey'] : o['OutputValue'] for o in outputs if o['OutputKey'].endswith(key)}

def lights_out(args):
    if args.dry_run:
        echo_args(args)
        return {}

    cf = boto3.resource('cloudformation', region_name = args.region)

    cf_c = cf.meta.client
    resources = cf_c.get_template(StackName = args.stack_name)['TemplateBody']['Resources']
    asg_mins = {k : v['Properties']['MinSize'] for k, v in resources.items() if k.endswith('ASG')}

    asg_ids = output_dict_ending(cf.Stack(args.stack_name).outputs, 'ASG')
    
    autoscale = boto3.client('autoscaling', region_name = args.region)
    for logical, physical in asg_ids.iteritems():
        autoscale.update_auto_scaling_group(
            AutoScalingGroupName = physical,
            MinSize = asg_mins[logical],
            DesiredCapacity = asg_mins[logical])

    return asg_mins

def echo_args(args):
    for k, v in vars(args).iteritems():
        print '{} : {}'.format(k, v)

def get_args():
    ap = argparse.ArgumentParser(description = 'Scale all ASGs in a stack back to their stack defaults')
    ap.add_argument('stack_name', help='Name of the stack')
    ap.add_argument('-?', '--dry-run', action = 'count', default = False, help = 'Echo parameters; take no action')
    ap.add_argument('-r', '--region', default = 'us-west-2', help = 'AWS Region in which to run')
    
    return ap.parse_args()

if __name__ == '__main__':
    args = get_args()
    results = lights_out(args)
    for asg_name, min_size in results.iteritems():
        print 'ASG scaled to min {}: {}'.format(asg_name, min_size)




