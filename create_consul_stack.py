#!/usr/bin/python

import argparse
from datetime import datetime
import inspect
import os

import boto3

import arguments
from scaffold import stack
from scaffold.stack.creator import StackCreator
from scaffold.consul.consul_template import ConsulTemplate


class ConsulCreator(StackCreator):
    def __init__(self, args, session):
        super(ConsulCreator, self).__init__(args.stack_name, session)
        self.args = args

    def get_s3_bucket(self):
        return self.args.s3_bucket

    def create_s3_key_prefix(self):
        return '{}/consul-{}'.format(self.args.s3_key_prefix, datetime.utcnow().strftime('%Y%m%d-%H%M%S'))

    def get_dependencies(self, dependencies):
        outputs = stack.outputs(self.session, args.network_stack_name)

        dependencies.vpc_id = outputs['VpcId']
        dependencies.vpc_cidr = outputs['VpcCidr']
        dependencies.private_subnet_ids = outputs.values(lambda k: 'PrivateSubnet' in k)
        dependencies.public_subnet_ids = outputs.values(lambda k: 'PublicSubnet' in k)

    def create_template(self, dependencies):
        return ConsulTemplate(
            self.stack_name,
            region=self.get_region(),
            bucket=self.get_s3_bucket(),
            key_prefix=dependencies.s3_key_prefix,
            vpc_id=dependencies.vpc_id,
            vpc_cidr=dependencies.vpc_cidr,
            server_subnet_ids=dependencies.private_subnet_ids,
            ui_subnet_ids=dependencies.public_subnet_ids,
            description=self.args.desc,
            server_cluster_size=self.args.cluster_size,
            server_instance_type=self.args.instance_type,
            ui_instance_type=self.args.ui_instance_type
        )

    def do_before_create(self, dependencies, dry_run):
        base_dir = os.path.dirname(inspect.getfile(ConsulTemplate))
        base_dir = os.path.join(base_dir, 'config')

        s3 = self.session.resource('s3')
        bucket = s3.Bucket(self.get_s3_bucket())
        for dir_name, dir_list, file_list in os.walk(base_dir):
            for file_name in file_list:
                file_path = os.path.join(dir_name, file_name)
                key_path = '/'.join((dependencies.s3_key_prefix, os.path.relpath(file_path, base_dir)))
                with open(file_path, 'r') as f:
                    bucket.put_object(Key=key_path,
                                      Body=f.read())

    def get_stack_parameters(self):
        return {
            ConsulTemplate.CONSUL_KEY_PARAM_NAME: self.args.consul_key
        }


def create_stack(args):
    creator = ConsulCreator(args, boto3.session.Session(profile_name=args.profile))
    return creator.create(args.dry_run)


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
    if results.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack.stack_id
        print 'STATUS: ', results.stack.stack_status
        if results.stack.stack_status_reason is not None:
            print 'REASON: ', results.stack.stack_status_reason
