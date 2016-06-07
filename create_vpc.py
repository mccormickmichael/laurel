#!/usr/bin/python

import argparse
from datetime import datetime

import boto3

import arguments
from scaffold.network.vpc_template import VpcTemplate
from scaffold.stack.creator import StackCreator


class VpcCreator(StackCreator):
    def __init__(self, args, session):
        super(VpcCreator, self).__init__(args.stack_name, session)
        self.args = args

    def get_s3_bucket(self):
        return self.args.s3_bucket

    def create_s3_key_prefix(self):
        return '{}/vpc-{}'.format(self.args.s3_key_prefix, datetime.utcnow().strftime('%Y%m%d-%H%M%S'))

    def create_template(self, dependent_ouptuts):
        return VpcTemplate(self.args.stack_name,
                           region=self.get_region(),
                           description=self.args.desc,  # TODO: which is better? more typing or more implicitness?
                           vpc_cidr=self.args.cidr,
                           availability_zones=self.args.availability_zones,
                           pub_size=self.args.pub_size,
                           priv_size=self.args.priv_size)


def create_stack(args):
    creator = VpcCreator(args, boto3.session.Session(profile_name=args.profile))
    return creator.create(args.dry_run)


default_desc = 'Network Stack'
default_cidr = '172.16.0.0/18'
default_azs = ['a', 'b', 'c']
default_pub_size = 1024
default_priv_size = 2048


def get_args():
    ap = argparse.ArgumentParser(description='Create a VPC CloudFormation stack with N public and private subnets',
                                 add_help=False)
    req = ap.add_argument_group('Required arguments')
    req.add_argument("stack_name",
                     help='Name of the network stack to create')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc', default=default_desc,
                    help=arguments.generate_help('Stack description.', default_desc))
    st.add_argument('--cidr', default=default_cidr,
                    help=arguments.generate_help('CIDR block of the VPC.', default_cidr))
    st.add_argument('--availability-zones', default=default_azs, nargs='+', metavar='AZ',
                    help=arguments.generate_help('Space-separated list of availability zones to use. Will determine the number of subnets.', default_azs))
    st.add_argument('--pub-size', default=default_pub_size, type=int, metavar='SIZE',
                    help=arguments.generate_help('Size of the public subnets.', default_pub_size))
    st.add_argument('--priv-size', default=default_priv_size, type=int, metavar='SIZE',
                    help=arguments.generate_help('Size of the private subnets.', default_priv_size))

    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)

    return ap.parse_args()


if __name__ == "__main__":
    args = get_args()
    results = create_stack(args)
    if results.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack.stack_id
        print 'STATUS: ', results.stack.stack_status
        if results.stack.stack_status_reason is not None:
            print 'REASON: ', results.stack.stack_status_reason
