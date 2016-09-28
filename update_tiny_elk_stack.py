#!/usr/bin/python

import argparse

import arguments
import logconfig
import session
from app.elk.tiny_builder import TinyElkBuilder


def update_stack(args):
    boto3_session = session.new(args.profile, args.region, args.role)
    builder = TinyElkBuilder(args, boto3_session, True)
    return builder.build(args.dry_run)


def get_args():
    ap = argparse.ArgumentParser(description='Updates an existing CloudFormation stack hosting a tiny ELK stack: 1 server for Logstash/Elasticsearch, 1 server for Kibana',
                                 add_help=False)
    req = ap.add_argument_group('Required')
    req.add_argument('stack_name',
                     help='Name of the ELK stack to update`')
    req.add_argument('network_stack_name',
                     help='Name of the network stack')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc',
                    help='Stack description.')
    st.add_argument('--server-key',
                    help='Name of the key pair used to access the ELK server instances.')
    st.add_argument('--es-instance-type',
                    help='Instance type for the Elasticsearch server.')
    st.add_argument('--kibana-instance-type',
                    help='Instance type for the Kibana server.')

    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)
    return ap.parse_args()


if __name__ == '__main__':
    logconfig.config()
    args = get_args()
    results = update_stack(args)
    # TODO: move these to logging messages
    if results.dry_run:
        print results.template
    else:
        print 'ID:     ', results.stack.stack_id
        print 'STATUS: ', results.stack.stack_status
        if results.stack.stack_status_reason is not None:
            print 'REASON: ', results.stack.stack_status_reason
