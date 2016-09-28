#!/usr/bin/python

import argparse

import arguments
import logconfig
import session
from app.elk.tiny_builder import TinyElkBuilder


def create_stack(args):
    boto3_session = session.new(args.profile, args.region, args.role)
    builder = TinyElkBuilder(args, boto3_session, False)
    return builder.build(args.dry_run)


default_desc = 'Tiny ELK Stack'
default_es_instance_type = 't2.micro'
default_kibana_instance_type = 't2.micro'


def get_args():
    ap = argparse.ArgumentParser(description='Create a CloudFormation stack hosting a tiny ELK stack: 1 server for Logstash/Elasticsearch, 1 server for Kibana',
                                 add_help=False)
    req = ap.add_argument_group('Required')
    req.add_argument('stack_name',
                     help='Name of the ELK stack to create')
    req.add_argument('network_stack_name',
                     help='Name of the network stack')
    req.add_argument('--server-key', required=True,
                     help='Name of the key pair used to access the ELK server instances.')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc', default=default_desc,
                    help=arguments.generate_help('Stack description.', default_desc))
    st.add_argument('--es-instance-type', default=default_es_instance_type,
                    help=arguments.generate_help('Instance type for the Elasticsearch server.', default_es_instance_type))
    st.add_argument('--kibana-instance-type', default=default_kibana_instance_type,
                    help=arguments.generate_help('Instance type for the Kibana server.', default_kibana_instance_type))

    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)
    return ap.parse_args()


if __name__ == '__main__':
    logconfig.config()
    args = get_args()
    results = create_stack(args)
    # TODO: move these to logging messages
    if results.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack.stack_id
        print 'STATUS: ', results.stack.stack_status
        if results.stack.stack_status_reason is not None:
            print 'REASON: ', results.stack.stack_status_reason
