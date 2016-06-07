#!/usr/bin/python

import argparse
from datetime import datetime

import boto3

import arguments
from scaffold import stack
from scaffold.stack.builder import StackBuilder
from scaffold.services.services_template import ServicesTemplate


class ServicesBuilder(StackBuilder):
    def __init__(self, args, session):
        super(ServicesBuilder, self).__init__(args.stack_name, session)
        self.args = args

    def get_s3_bucket(self):
        return self.args.s3_bucket

    def create_s3_key_prefix(self):
        return '{}/services-{}'.format(self.args.s3_key_prefix, datetime.utcnow().strftime('%Y%m%d-%H%M%S'))

    def get_dependencies(self, dependencies):
        outputs = stack.outputs(self.session, self.args.network_stack_name)

        dependencies.vpc_id = outputs['VpcId']
        dependencies.vpc_cidr = outputs['VpcCidr']
        dependencies.priv_rt_id = outputs['PrivateRT']
        dependencies.public_subnet_ids = outputs.values(lambda k: 'PublicSubnet' in k)

        return dependencies

    def create_template(self, dependencies):
        return ServicesTemplate(
            self.stack_name,
            description=self.args.desc,
            vpc_id=dependencies.vpc_id,
            vpc_cidr=dependencies.vpc_cidr,
            private_route_table_id=dependencies.priv_rt_id,
            public_subnet_ids=dependencies.public_subnet_ids,
            bastion_instance_type=self.args.bastion_type,
            nat_instance_type=self.args.nat_type
        )

    def get_stack_parameters(self):
        return {
            ServicesTemplate.BASTION_KEY_PARM_NAME: self.args.bastion_key
        }


def create_stack(args):
    session = boto3.session.Session(profile_name=args.profile)
    builder = ServicesBuilder(args, session, False)
    return builder.build(args.dry_run)


default_desc = 'Services Stack'
default_bastion_type = 't2.micro'
default_nat_type = 't2.micro'


def get_args():
    ap = argparse.ArgumentParser(description='Create a stack containing a NAT and Bastion server',
                                 add_help=False)
    req = ap.add_argument_group('Required')
    req.add_argument('stack_name',
                     help='Name of the services stack to create')
    req.add_argument('network_stack_name',
                     help='Name of the network stack')
    req.add_argument('--bastion-key', required=True,
                     help='Name of the key pair to access the bastion server.')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc', default=default_desc,
                    help=arguments.generate_help('Stack description.', default_desc))
    st.add_argument('--bastion-type', default=default_bastion_type,
                    help=arguments.generate_help('Instance type of the Bastion server.', default_bastion_type))
    st.add_argument('--nat-type', default=default_nat_type,
                    help=arguments.generate_help('Instance type of the NAT server.', default_nat_type))

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
