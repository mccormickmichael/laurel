#!/usr/bin/python

import argparse

import boto3

from scaffold.network.vpc_nxn import NxNVPC
from scaffold.stack.operation import StackOperation
from scaffold.doby import Doby


def create_stack(args):
    session = boto3.session.Session(profile_name=args.profile)

    template = NxNVPC(args.stack_name,
                      region=session.region_name,
                      description=args.desc,
                      vpc_cidr=args.cidr,
                      availability_zones=args.availability_zones,
                      pub_size=args.pub_size,
                      priv_size=args.priv_size)
    template.build_template()
    template_json = template.to_json()

    results = {'template': template_json}

    if args.dry_run:
        return Doby(results)

    creator = StackOperation(session, args.stack_name, template.to_json(), args.bucket, args.key_prefix)
    stack = creator.create()
    results['stack_id'] = stack.stack_id
    results['stack_status'] = stack.stack_status
    results['stack_status_reason'] = stack.stack_status_reason
    # the return values here suck. How can we do better?
    return Doby(results)


default_desc = 'Network Stack'
default_cidr = '172.16.0.0/18'
default_azs = ['a', 'b', 'c']
default_pub_size = 1024
default_priv_size = 2048
default_bucket = 'thousandleaves-us-west-2-laurel-deploy'
default_key_prefix = 'scaffold/templates'
default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='Create a VPC and Network CloudFormation stack with N public and N private subnets')
    ap.add_argument("stack_name",
                    help='Name of the network stack to create')

    ap.add_argument('--desc', default=default_desc,
                    help='Stack description. Strongy encouraged.')
    ap.add_argument('--cidr', default=default_cidr,
                    help='CIDR block of the VPC. Default: {}'.format(default_cidr))
    ap.add_argument('--availability-zones', default=default_azs, nargs='+', metavar='AZ',
                    help='Space-separated list of availability zones to use. Will determine the number of subnets. Default: {}'.format(default_azs))
    ap.add_argument('--pub-size', default=default_pub_size, type=int, metavar='SIZE',
                    help='Size of the public subnets. Default: {}'.format(default_pub_size))
    ap.add_argument('--priv-size', default=default_priv_size, type=int, metavar='SIZE',
                    help='Size of the private subnets. Default: {}'.format(default_priv_size))

    ap.add_argument('--bucket', default=default_bucket,
                    help='Name of the S3 bucket to which stack template files are uploaded. Default: {}'.format(default_bucket))
    ap.add_argument('--key-prefix', default=default_key_prefix,
                    help='Prefix to use when uploading stack template files to the bucket. Default: {}'.format(default_key_prefix))

    ap.add_argument('--profile', default=default_profile,
                    help='AWS Credential and Config profile to use. Default: {}'.format(default_profile))
    ap.add_argument('--dry-run', default=False, action='store_true',
                    help='Output the generated stack template. Take no action.')

    return ap.parse_args()


if __name__ == "__main__":
    args = get_args()
    results = create_stack(args)
    if args.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack_id
        print 'STATUS: ', results.stack_status
        if results.stack_status_reason is not None:
            print 'REASON: ', results.stack_status_reason
