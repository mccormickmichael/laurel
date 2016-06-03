#!/usr/bin/python

import argparse

import boto3

from scaffold import stack
from scaffold.stack.operation import StackOperation
from scaffold.services.services_template import ServicesTemplate
from scaffold.doby import Doby


def create_stack(args):
    session = boto3.session.Session(profile_name=args.profile)

    outputs = stack.outputs(session, args.network_stack_name)

    vpc_id = outputs['VpcId']
    vpc_cidr = outputs['VpcCidr']
    priv_rt_id = outputs['PrivateRT']
    pub_subnet_ids = outputs.values(lambda k: 'PublicSubnet' in k)

    template = ServicesTemplate(
        args.stack_name,
        description=args.desc,
        vpc_id=vpc_id,
        vpc_cidr=vpc_cidr,
        private_route_table_id=priv_rt_id,
        public_subnet_ids=pub_subnet_ids,
        bastion_instance_type=args.bastion_type,
        nat_instance_type=args.nat_type
    )
    template.build_template()
    template_json = template.to_json()

    results = {'template': template_json}
    if args.dry_run:
        return Doby(results)

    stack_parms = {
        ServicesTemplate.BASTION_KEY_PARM_NAME: args.bastion_key
    }

    creator = StackOperation(session, args.stack_name, template_json, args.s3_bucket, args.s3_key_prefix)
    new_stack = creator.create(stack_parms)
    results['stack_id'] = new_stack.stack_id
    results['stack_status'] = new_stack.stack_status
    results['stack_status_reason'] = new_stack.stack_status_reason
    # the return values here suck. How can we do better?
    return Doby(results)


default_desc = 'Services Stack'
default_bastion_type = 't2.micro'
default_nat_type = 't2.micro'
default_s3_bucket = 'thousandleaves-us-west-2-laurel-deploy'
default_s3_key_prefix = 'scaffold/templates'
default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='Create a stack containing a NAT and Bastion server')
    ap.add_argument('stack_name',
                    help='Name of the services stack to create')
    ap.add_argument('network_stack_name',
                    help='Name of the network stack')

    ap.add_argument('--desc', default=default_desc,
                    help='Stack description. Strongy encouraged.')
    ap.add_argument('--bastion-key', required=True,
                    help='Name of the key pair to access the bastion server. Required.')

    ap.add_argument('--s3-bucket', default=default_s3_bucket,
                    help='Name of the S3 bucket to which stack template files are uploaded. Default: {}'.format(default_s3_bucket))
    ap.add_argument('--s3-key-prefix', default=default_s3_key_prefix,
                    help='Prefix to use when uploading stack template files to the bucket. Default: {}'.format(default_s3_key_prefix))

    ap.add_argument('--bastion-type', default=default_bastion_type,
                    help='Instance type of the Bastion server. Default: {}'.format(default_bastion_type))
    ap.add_argument('--nat-type', default=default_nat_type,
                    help='Instance type of the NAT server. Default: {}'.format(default_nat_type))

    ap.add_argument('--profile', default=default_profile,
                    help='AWS Credential and Config profile to use. Default: {}'.format(default_profile))
    ap.add_argument('--dry-run', action='store_true', default=False,
                    help='Echo the parameters to be used to create the stack; take no action')
    return ap.parse_args()


if __name__ == '__main__':
    args = get_args()
    results = create_stack(args)
    if args.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack_id
        print 'STATUS: ', results.stack_status
        if results.stack_status_reason is not None:
            print 'REASON: ', results.stack_status_reason
