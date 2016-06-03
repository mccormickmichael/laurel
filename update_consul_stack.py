#!/usr/bin/python

import argparse
import inspect
import os

import boto3

from scaffold.stack import Parameters, Summary
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


def update_stack(args):
    session = boto3.session.Session(profile_name=args.profile)

    summary = Summary(session, args.stack_name)
    build_parms = summary.build_parameters()

    template = ConsulTemplate(
        args.stack_name,
        region=session.region_name,
        bucket=build_parms.bucket if args.s3_bucket is None else args.s3_bucket,
        vpc_id=build_parms.vpc_id,
        vpc_cidr=build_parms.vpc_cidr,
        server_subnet_ids=build_parms.server_subnet_ids,
        ui_subnet_ids=build_parms.ui_subnet_ids,
        description=summary.description() if args.desc is None else args.desc,
        server_cluster_size=build_parms.server_cluster_size if args.cluster_size is None else args.cluster_size,
        server_instance_type=build_parms.server_instance_type if args.instance_type is None else args.instance_type,
        ui_instance_type=build_parms.ui_instance_type if args.ui_instance_type is None else args.ui_instance_type
    )
    template.build_template()
    template_json = template.to_json()

    results = {'template': template_json}
    if args.dry_run:
        return Doby(results)

    basedir = os.path.dirname(inspect.getfile(ConsulTemplate))
    upload_config(session, args.s3_bucket, 'scaffold', basedir)  # TODO: replace 'scaffold' with args.key_prefix

    cf = session.resource('cloudformation')
    current_parms = Parameters(cf.Stack(args.stack_name))

    stack_parms = {
        ConsulTemplate.CONSUL_KEY_PARAM_NAME:
        current_parms[ConsulTemplate.CONSUL_KEY_PARAM_NAME] if args.consul_key is None else args.consul_key
    }

    updater = StackOperation(session, args.stack_name, template_json, args.s3_bucket, args.s3_key_prefix)
    stack = updater.update(stack_parms)
    results['stack_id'] = stack.stack_id
    results['stack_status'] = stack.stack_status
    results['stack_status_reason'] = stack.stack_status_reason
    # the return values here suck. How can we do better?
    return Doby(results)


default_s3_bucket = 'thousandleaves-us-west-2-laurel-deploy'
default_s3_key_prefix = 'scaffold/templates'
default_profile = 'default'


def get_args():
    ap = argparse.ArgumentParser(description='Create a CloudFormation stack hosting a Consul cluster')
    ap.add_argument('stack_name',
                    help='Name of the Consul stack to create')

    ap.add_argument('--desc',
                    help='Stack description. Strongy encouraged.')
    ap.add_argument('--consul-key',
                    help='Name of the key pair used to access the Consul cluster instances.')
    ap.add_argument('--instance-type',
                    help='Instance type for the Consul servers.')
    ap.add_argument('--ui-instance-type',
                    help='Instance type for the Consul UI servers.')
    ap.add_argument('--cluster_size',
                    help='Number of instances in the Consul cluster. Should be an odd number > 1.')

    ap.add_argument('--s3-bucket', default=default_s3_bucket,
                    help='Name of the S3 bucket to which stack template files are uploaded. Default: {}'.format(default_s3_bucket))
    ap.add_argument('--s3-key-prefix', default=default_s3_key_prefix,
                    help='Prefix to use when uploading stack template files to the bucket. Default: {}'.format(default_s3_key_prefix))


    ap.add_argument('--profile', default=default_profile,
                    help='AWS Credential and Config profile to use. Default: {}'.format(default_profile))
    ap.add_argument('--dry-run', action='store_true', default=False,
                    help='Echo the parameters to be used to create the stack; take no action')
    return ap.parse_args()

if __name__ == '__main__':
    args = get_args()
    results = update_stack(args)
    if args.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack_id
        print 'STATUS: ', results.stack_status
        if results.stack_status_reason is not None:
            print 'REASON: ', results.stack_status_reason

