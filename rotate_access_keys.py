import argparse
import ConfigParser
import os.path

import boto3

import arguments


def rotate_keys(args):
    session = boto3.session.Session(profile_name=args.profile)
    iam = session.resource('iam')
    if args.user is not None:
        user = iam.User(args.user)
    else:
        user = iam.CurrentUser().user
    keys = sorted(user.access_keys.all(), key=lambda x: x.create_date)
    if args.dry_run:
        for key in keys:
            print_key(key)

    if len(keys) > 1:
        oldest_key = keys[0]
        if args.dry_run:
            print 'rotate_keys would delete key {} but dry-run flag is set.'.format(oldest_key.id)
            return None
        print 'deleting key {}'.format(oldest_key.id)
        oldest_key.delete()

    if args.dry_run:
        print 'not creating a new key because dry-run flag is set'
        return None

    return user.create_access_key_pair()


def print_key(access_key):
    print 'USER  : {}'.format(access_key.user_name)
    print 'DATE  : {}'.format(access_key.create_date)
    print 'STATUS: {}'.format(access_key.status)
    print 'KEY ID: {}'.format(access_key.id)


def print_key_pair(access_key):
    print_key(access_key)
    print 'SECRET: {}'.format(access_key.secret)


def write_key_pair(access_key, creds_file, profile):
    creds_file = os.path.expanduser(creds_file)
    creds = ConfigParser.ConfigParser()
    print 'using {}'.format(creds_file)
    with open(creds_file, 'r') as f:
        creds.readfp(f)
    if profile != 'default' and not creds.has_section(profile):
        creds.add_section(profile)
    creds.set(profile, 'aws_access_key_id', access_key.id)
    creds.set(profile, 'aws_secret_access_key', access_key.secret)
    with open(creds_file, 'w') as f:
        creds.write(f)


default_creds_file = '~/.aws/credentials'


def get_args():
    ap = argparse.ArgumentParser(description='Rotate access keys. Optionally save the new key and secret to your aws credentials file.',
                                 add_help=False)

    km = ap.add_argument_group('Key management')
    km.add_argument('--user',
                    help='Rotate keys for specific user. Defaults to current user.')
    km.add_argument('--credentials', default=default_creds_file,
                    help=arguments.generate_help('Location of the credentials file to modify.', default_creds_file))
    km.add_argument('--no-persist', default=False, action='store_true',
                    help='Do not persist key and secret to credentials file. Instead, print key and secret to stdout.')

    arguments.add_security_control_group(ap)  # TODO: no dry-run option

    return ap.parse_args()


if __name__ == '__main__':
    args = get_args()
    new_key = rotate_keys(args)
    if new_key is not None:
        if args.no_persist is True:
            print_key_pair(new_key)
        else:
            write_key_pair(new_key, args.credentials, args.profile)
            print 'KEY ID: {}'.format(new_key.id)
