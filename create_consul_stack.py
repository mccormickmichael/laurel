#!/usr/bin/python

import argparse
import inspect
import os

import boto3

from scaffold.stack import Outputs
from scaffold.stack.operation import StackOperation
from scaffold.consul.consul_template import ConsulTemplate
from scaffold.doby import Doby


def upload_config(session, bucket_name, key_prefix, base_dir):
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)
    base_dir = os.path.join(base_dir, 'config')
    key_prefix = '/'.join((key_prefix, 'consul'))
    for dir_name, dir_list, file_list in os.walk(base_dir):
        for file_name in file_list:
            file_path = os.path.join(dir_name, file_name)
            key_path = '/'.join((key_prefix, os.path.relpath(file_path, base_dir)))
            with open(file_path, 'r') as f:
                bucket.put_object(Key=key_path,
                                  Body=f.read())


def create_stack(args):
    session = boto3.session.Session(profile_name=args.profile)

    cf = session.resource('cloudformation')
    outputs = Outputs(cf.Stack(args.network_stack_name))

    vpc_id = outputs['VpcId']
    vpc_cidr = outputs['VpcCidr']
    private_subnet_ids = outputs.values(lambda k: 'PrivateSubnet' in k)
    public_subnet_ids = []  # TODO: outputs.values(lambda k: 'PublicSubnet' in k)

    template = ConsulTemplate(
        args.stack_name,
        region=session.region_name,
        bucket=args.s3_bucket,
        vpc_id=vpc_id,
        vpc_cidr=vpc_cidr,
        server_subnet_ids=private_subnet_ids,
        ui_subnet_ids=public_subnet_ids,
        description=args.desc,
        server_cluster_size=args.cluster_size,
        server_instance_type=args.instance_type,
        ui_instance_type=args.ui_instance_type
    )
    template.build_template()
    template_json = template.to_json()

    results = {'template': template_json}
    basedir = os.path.dirname(inspect.getfile(ConsulTemplate))

    upload_config(session, args.s3_bucket, 'scaffold', basedir)  # TODO: replace 'scaffold' with args.key_prefix

    if args.dry_run:
        return Doby(results)

    stack_parms = {
        ConsulTemplate.CONSUL_KEY_PARAM_NAME: args.consul_key
    }

    creator = StackOperation(session, args.stack_name, template_json, args.s3_bucket, args.s3_key_prefix)
    stack = creator.create(stack_parms)
    results['stack_id'] = stack.stack_id
    results['stack_status'] = stack.stack_status
    results['stack_status_reason'] = stack.stack_status_reason
    # the return values here suck. How can we do better?
    return Doby(results)


default_desc = 'Consul Stack'
default_instance_type = 't2.micro'
default_ui_instance_type = 't2.micro'
default_cluster_size = 3
default_s3_bucket = 'thousandleaves-us-west-2-laurel-deploy'
default_s3_key_prefix = 'scaffold/templates'
default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='Create a CloudFormation stack hosting a Consul cluster')
    ap.add_argument('stack_name',
                    help='Name of the Consul stack to create')
    ap.add_argument('network_stack_name',
                    help='Name of the network stack')

    ap.add_argument('--desc', default=default_desc,
                    help='Stack description. Strongy encouraged.')
    ap.add_argument('--consul-key', required=True,
                    help='Name of the key pair used to access the Consul cluster instances. Required.')

    ap.add_argument('--s3-bucket', default=default_s3_bucket,
                    help='Name of the S3 bucket to which stack template files are uploaded. Default: {}'.format(default_s3_bucket))
    ap.add_argument('--s3-key-prefix', default=default_s3_key_prefix,
                    help='Prefix to use when uploading stack template files to the bucket. Default: {}'.format(default_s3_key_prefix))

    ap.add_argument('--instance-type', default=default_instance_type,
                    help='Instance type for the Consul servers. Default: {}'.format(default_instance_type))
    ap.add_argument('--ui-instance-type', default=default_ui_instance_type,
                    help='Instance type for the Consul UI servers. Default: {}'.foramt(default_ui_instance_type))
    ap.add_argument('--cluster_size', default=default_cluster_size,
                    help='Number of instances in the Consul cluster. Should be an odd number > 1. Default: {}'.format(default_cluster_size))

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
