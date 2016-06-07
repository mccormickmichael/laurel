#!/usr/bin/python

import argparse
from datetime import datetime

import boto3

import arguments
from scaffold.network.vpc_template import VpcTemplate
from scaffold.stack.operation import StackOperation
from scaffold.stack import Summary
from scaffold.doby import Doby


def update_stack(args):
    key_prefix = '{}/vpc_nxn-{}'.format(args.s3_key_prefix, datetime.utcnow().strftime('%Y%m%d-%H%M%S'))
    session = boto3.session.Session(profile_name=args.profile)

    summary = Summary(session, args.stack_name)
    build_parms = summary.build_parameters()

    template = VpcTemplate(
        args.stack_name,
        region=session.region_name,
        description=summary.description() if args.desc is None else args.desc,
        vpc_cidr=build_parms.vpc_cidr if args.cidr is None else args.cidr,
        availability_zones=build_parms.availability_zones if args.availability_zones is None else args.availability_zones,
        pub_size=build_parms.pub_size if args.pub_size is None else args.pub_size,
        priv_size=build_parms.priv_size if args.priv_size is None else args.priv_size
    )

    template.build_template()
    template_json = template.to_json()

    results = {'template': template_json}

    if args.dry_run:
        return Doby(results)

    updater = StackOperation(session, args.stack_name, template_json, args.s3_bucket, key_prefix)
    stack = updater.update()
    results['stack_id'] = stack.stack_id
    results['stack_status'] = stack.stack_status
    results['stack_status_reason'] = stack.stack_status_reason
    # the return values here suck. How can we do better?
    return Doby(results)


def get_args():
    ap = argparse.ArgumentParser(description='''Update a CloudFormation stack created with 'create_vpc'.''',
                                 add_help=False)
    ap.add_argument("stack_name",
                    help='Name of the network stack to create')

    ap.add_argument('--desc',
                    help='Stack description. Strongy encouraged.')
    ap.add_argument('--cidr',
                    help='CIDR block of the VPC.')
    ap.add_argument('--availability-zones', nargs='+', metavar='AZ',
                    help='Space-separated list of availability zones to use. Will determine the number of subnets.')
    ap.add_argument('--pub-size', type=int, metavar='SIZE',
                    help='Size of the public subnets.')
    ap.add_argument('--priv-size', type=int, metavar='SIZE',
                    help='Size of the private subnets.')

    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)

    return ap.parse_args()


if __name__ == "__main__":
    args = get_args()
    results = update_stack(args)
    if args.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack_id
        print 'STATUS: ', results.stack_status
        if results.stack_status_reason is not None:
            print 'REASON: ', results.stack_status_reason
