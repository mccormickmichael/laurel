#!/usr/bin/python

import argparse
from datetime import datetime

import boto3

import arguments
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


def get_args():
    ap = argparse.ArgumentParser(description='''Update a CloudFormation stack created with 'create_service_stack'.''',
                                 add_help=False)
    req = ap.add_argument_group('Required')
    req.add_argument("stack_name",
                     help='Name of the service stack to update')
    req.add_argument('--bastion-key', required=True,
                     help='Name of the key pair to access the bastion server.')

    st = ap.add_argument_group('Stack definitions')
    st.add_argument('--desc',
                    help='Stack description.')
    st.add_argument('--bastion-type',
                    help='Instance type of the Bastion server.')
    st.add_argument('--nat-type',
                    help='Instance type of the NAT server.')

    arguments.add_deployment_group(ap)
    arguments.add_security_control_group(ap)
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
