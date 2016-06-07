#!/usr/bin/python

import argparse
from datetime import datetime
import inspect
import os

import boto3

import arguments
from scaffold import stack
from scaffold.stack.operation import StackOperation
from scaffold.consul.consul_template import ConsulTemplate
from scaffold.doby import Doby


def upload_config(session, bucket_name, key_prefix, base_dir):
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)
    base_dir = os.path.join(base_dir, 'config')
    for dir_name, dir_list, file_list in os.walk(base_dir):
        for file_name in file_list:
            file_path = os.path.join(dir_name, file_name)
            key_path = '/'.join((key_prefix, os.path.relpath(file_path, base_dir)))
            with open(file_path, 'r') as f:
                bucket.put_object(Key=key_path,
                                  Body=f.read())


def create_stack(args):
    key_prefix = '{}/consul-{}'.format(args.s3_key_prefix, datetime.utcnow().strftime('%Y%m%d-%H%M%S'))
    session = boto3.session.Session(profile_name=args.profile)

    outputs = stack.outputs(session, args.network_stack_name)

    vpc_id = outputs['VpcId']
    vpc_cidr = outputs['VpcCidr']
    private_subnet_ids = outputs.values(lambda k: 'PrivateSubnet' in k)
    public_subnet_ids = outputs.values(lambda k: 'PublicSubnet' in k)

    template = ConsulTemplate(
        args.stack_name,
        region=session.region_name,
        bucket=args.s3_bucket,
        key_prefix=key_prefix,
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
    upload_config(session, args.s3_bucket, key_prefix, basedir)

    stack_parms = {
        ConsulTemplate.CONSUL_KEY_PARAM_NAME: args.consul_key
    }

    creator = StackOperation(session, args.stack_name, template_json, args.s3_bucket, key_prefix)
    if args.dry_run:
        return Doby(results)

    new_stack = creator.create(stack_parms)
    results['stack_id'] = new_stack.stack_id
    results['stack_status'] = new_stack.stack_status
    results['stack_status_reason'] = new_stack.stack_status_reason
    # the return values here suck. How can we do better?
    return Doby(results)


default_desc = 'Consul Stack'
default_instance_type = 't2.micro'
default_ui_instance_type = 't2.micro'
default_cluster_size = 3


def get_args():
    ap = argparse.ArgumentParser(description='Create a CloudFormation stack hosting a Consul cluster',
                                 add_help=False)
    req = ap.add_argument_group('Required')
    ap.add_argument('stack_name',
                    help='Name of the Consul stack to create')
    req.add_argument('network_stack_name',
                     help='Name of the network stack')
    req.add_argument('--consul-key', required=True,
                     help='Name of the key pair used to access the Consul cluster instances.')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc', default=default_desc,
                    help=arguments.generate_help('Stack description.', default_desc))
    st.add_argument('--instance-type', default=default_instance_type,
                    help=arguments.generate_help('Instance type for the Consul servers.', default_instance_type))
    st.add_argument('--ui-instance-type', default=default_ui_instance_type,
                    help=arguments.generate_help('Instance type for the Consul UI servers.', default_ui_instance_type))
    st.add_argument('--cluster_size', default=default_cluster_size,
                    help=arguments.generate_help('Number of instances in the Consul cluster. Should be an odd number > 1.', default_cluster_size))
    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)
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
