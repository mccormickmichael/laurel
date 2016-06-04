#!/usr/bin/python

import argparse
from datetime import datetime

import boto3

from scaffold.services.services_template import ServicesTemplate
from scaffold.stack.operation import StackOperation
from scaffold.stack import Summary
from scaffold.doby import Doby


def update_stack(args):
    key_prefix = '{}/service-{}'.format(args.s3_key_prefix, datetime.utcnow().strftime('%Y%m%d-%H%M%S'))
    session = boto3.session.Session(profile_name=args.profile)

    summary = Summary(session, args.stack_name)
    build_parms = summary.build_parameters()

    template = ServicesTemplate(
        args.stack_name,
        description=summary.description() if args.desc is None else args.desc,
        vpc_id=build_parms.vpc_id,
        vpc_cidr=build_parms.vpc_cidr,
        private_route_table_id=build_parms.private_route_table_id,
        public_subnet_ids=build_parms.public_subnet_ids,
        bastion_instance_type=build_parms.bastion_instance_type if args.bastion_type is None else args.bastion_type,
        nat_instance_type=build_parms.nat_instance_type if args.nat_type is None else args.nat_type
    )
    template.build_template()
    template_json = template.to_json()

    results = {'template': template_json}

    if args.dry_run:
        return Doby(results)

    stack_parms = {}
    if args.bastion_key is not None:
        stack_parms[ServicesTemplate.BASTION_KEY_PARM_NAME] = args.bastion_key

    updater = StackOperation(session, args.stack_name, template_json, args.s3_bucket, key_prefix)
    stack = updater.update(stack_parms)
    results['stack_id'] = stack.stack_id
    results['stack_status'] = stack.stack_status
    results['stack_status_reason'] = stack.stack_status_reason
    # the return values here suck. How can we do better?
    return Doby(results)


default_bastion_type = 't2.micro'
default_nat_type = 't2.micro'
default_s3_bucket = 'thousandleaves-us-west-2-laurel-deploy'
default_s3_key_prefix = 'scaffold'
default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='''Update a CloudFormation stack created with 'create_service_stack'.''')
    ap.add_argument("stack_name",
                    help='Name of the service stack to update')

    ap.add_argument('--desc',
                    help='Stack description. Strongy encouraged.')
    ap.add_argument('--bastion-key', required=True,
                    help='Name of the key pair to access the bastion server. Required.')
    ap.add_argument('--bastion-type', default=default_bastion_type,
                    help='Instance type of the Bastion server. Default: {}'.format(default_bastion_type))
    ap.add_argument('--nat-type', default=default_nat_type,
                    help='Instance type of the NAT server. Default: {}'.format(default_nat_type))


    ap.add_argument('--s3-bucket', default=default_s3_bucket,
                    help='Name of the S3 bucket to which stack template files are uploaded. Default: {}'.format(default_s3_bucket))
    ap.add_argument('--s3-key-prefix', default=default_s3_key_prefix,
                    help='Prefix to use when uploading stack template files to the bucket. Default: {}'.format(default_s3_key_prefix))

    ap.add_argument('--profile', default=default_profile,
                    help='AWS Credential and Config profile to use. Default: {}'.format(default_profile))
    ap.add_argument('--dry-run', default=False, action='store_true',
                    help='Output the generated stack template. Take no action.')
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
