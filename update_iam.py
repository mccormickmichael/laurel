# Update the users and groups and roles based on the users.yml and groups.yml and roles.yml files.
# Users missing from users.yml are not deleted.
# Groups missing from groups.yml are not deleted.


import argparse
import logging
import os.path

import boto3
import yaml

import arguments
from scaffold.iam.group_sync import GroupSync
from scaffold.iam.user_sync import UserSync
from scaffold.iam.role_sync import RoleSync
from scaffold.iam.policy_sync import PolicySync


def get_session(args):
    return boto3.session.Session(profile_name=args.profile, region_name=args.region)


def userspath(basedir):
    return os.path.join(basedir, 'users.yml')


def groupspath(basedir):
    return os.path.join(basedir, 'groups.yml')


def rolespath(basedir):
    return os.path.join(basedir, 'roles.yml')


def policypath(basedir):
    return os.path.join(basedir, 'policies')


def update_groups(args, session):
    with open(groupspath(args.basedir), 'r') as f:
        groups = yaml.load(f)
    synchronizer = GroupSync(session, args.iam_stack)
    synchronizer.sync(groups, args.dry_run)
    # TODO: results? Provide list of groups impacted?


def update_users(args, session):
    with open(userspath(args.basedir), 'r') as f:
        users = yaml.load(f)
    synchronizer = UserSync(session)
    synchronizer.sync(users, args.dry_run)
    # TODO: results? Provide list of users impacted?


def update_roles(args, session):
    with open(rolespath(args.basedir), 'r') as f:
        roles = yaml.load(f)
    synchronizer = RoleSync(session, args.iam_stack)
    synchronizer.sync(roles, args.dry_run)
    # TODO: results? Provide list of roles impacted?


def update_policies(args, session):
    synchronizer = PolicySync(session)
    synchronizer.sync(policypath(args.basedir), args.dry_run)
    # TODO: results? Provide list of policies impacted?

def parse_args():
    ap = argparse.ArgumentParser(description='Update IAM elements: users, groups, roles, policies',
                                 add_help=False)
    ap.add_argument('basedir',
                    help='Directory containing IAM elements files. See security/README for details')
    ap.add_argument('--iam-stack', default=None,
                    help='Name of the IAM Cloudformation stack, if any.')
    arguments.add_security_control_group(ap)

    return ap.parse_args()


def validate_args(args):
    errors = []
    up = userspath(args.basedir)
    if not os.path.isfile(up):
        errors.append('The users file {} does not exist'.format(up))
    gp = groupspath(args.basedir)
    if not os.path.isfile(gp):
        errors.append('The groups file {} does not exist'.format(gp))
    rp = rolespath(args.basedir)
    if not os.path.isfile(rp):
        errors.append('The roles file {} does not exist'.format(rp))
    pp = policypath(args.basedir)
    if not os.path.isdir(pp):
        errors.append('The policy directory {} does not exist'.format(pp))

    if errors:
        raise ValueError('Unable to update elements: \n  {}'.format('\n  '.join(errors)))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(relativeCreated)6d:%(levelname)5s:%(name)s:%(message)s')
    for name in ['boto3', 'botocore']:
        logging.getLogger(name).setLevel(logging.WARN)  # MEH.
    args = parse_args()
    validate_args(args)
    session = get_session(args)
    update_policies(args, session)
    update_groups(args, session)
    update_users(args, session)
    update_roles(args, session)
