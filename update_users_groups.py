# Update the users and groups and roles based on the users.yml and groups.yml and roles.yml files.
# Users missing from users.yml are not deleted.
# Groups missing from groups.yml are not deleted.


import argparse
import logging

import boto3
import yaml

import arguments
from scaffold.iam.group_sync import GroupSync
from scaffold.iam.user_sync import UserSync
from scaffold.iam.role_sync import RoleSync


def get_session(args):
    return boto3.session.Session(profile_name=args.profile, region_name=args.region)


def update_policies(args, session):
    pass


def update_groups(args, session):
    with open(args.groups, 'r') as f:
        groups = yaml.load(f)
    synchronizer = GroupSync(session, args.iam_stack)
    synchronizer.sync(groups, args.dry_run)
    # TODO: results? Provide list of groups impacted?


def update_users(args, session):
    with open(args.users, 'r') as f:
        users = yaml.load(f)
    synchronizer = UserSync(session)
    synchronizer.sync(users, args.dry_run)
    # TODO: results? Provide list of users impacted?


def update_roles(args, session):
    with open(args.roles, 'r') as f:
        roles = yaml.load(f)
    synchronizer = RoleSync(session, args.iam_stack)
    synchronizer.sync(roles, args.dry_run)
    # TODO: results? Provide list of roles impacted?


def parse_args():
    ap = argparse.ArgumentParser(description='Update users and groups',
                                 add_help=False)
    ap.add_argument('--users', default='users.yml',
                    help='Name of the users.yml file')
    ap.add_argument('--groups', default='groups.yml',
                    help='Name of the groups.yml file')
    ap.add_argument('--roles', default='roles.yml',
                    help='Name of the roles.yml file')
    ap.add_argument('--iam-stack', default=None,
                    help='Name of the IAM Cloudformation stack, if any.')
    ap.add_argument('--region', default='us-west-2',
                    help='Region to connect to. Default: us-west-2')
    arguments.add_security_control_group(ap)

    return ap.parse_args()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    for name in ['boto3', 'botocore']:
        logging.getLogger(name).setLevel(logging.WARN)  # MEH.
    args = parse_args()
    session = get_session(args)
    update_policies(args, session)
    update_groups(args, session)
    update_users(args, session)
    update_roles(args, session)
