# Update the users and groups based on the users.yml and groups.yml files.
# Users missing from users.yml are not deleted.

import argparse

import boto3
import yaml

import arguments
from scaffold.iam.group_sync import GroupSync
from scaffold.iam.user_sync import UserSync

def get_session(args):
    return boto3.session.Session(profile_name=args.profile)

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


def parse_args():
    ap = argparse.ArgumentParser(description='Update users and groups',
                                 add_help=False)
    ap.add_argument('--users', default='
users.yml',
                    help='Name of the users.yml file')
    ap.add_argument('--groups', default='groups.yml'
                    help='Name of the groups.yml file')
    ap.add_argument('--iam-stack', default=None,
                    help='Name of the IAM Cloudformation stack, if any.')
    arguments.add_security_control_group(ap)
    
    return ap.parse_args()
    

if __name__ == '__main__':
    args = parse_args()
    session = get_sesssion(args)
    update_groups(args, session)
    update_users(args, session)
