default_profile = 'default'
default_region_name = 'us-west-2'
default_deploy_s3_bucket = 'thousandleaves-us-west-2-laurel-deploy'
default_deploy_s3_key_prefix = 'scaffold'

deploy_s3_bucket_help = 'Name of the S3 bucket to which stack template files are uploaded.'
deploy_s3_key_prefix_help = 'Prefix to use when uploading stack template files to the bucket.'

profile_help = 'AWS Credential and Config profile to use.'
region_help = 'Region to connect to. Required if profile is specified.'
dry_run_help = 'Report on what would have happened. Take no mutable action.'


def add_deployment_group(argparser,
                         default_deploy_bucket=default_deploy_s3_bucket,
                         default_deploy_key_prefix=default_deploy_s3_key_prefix,
                         use_defaults=True):
    group = argparser.add_argument_group('Deployment')
    group.add_argument('--deploy-s3-bucket', default=default_deploy_s3_bucket if use_defaults else None,
                       help=generate_help(deploy_s3_bucket_help, default_deploy_s3_bucket, use_defaults))
    group.add_argument('--deploy-s3-key-prefix', default=default_deploy_s3_key_prefix if use_defaults else None,
                       help=generate_help(deploy_s3_key_prefix_help, default_deploy_s3_key_prefix, use_defaults))
    return group


def add_security_control_group(argparser,
                               default_profile_name='default',
                               add_help=True):
    group = argparser.add_argument_group('Security and control')
    group.add_argument('--profile', default=default_profile_name,
                       help=generate_help(profile_help, default_profile_name))
    group.add_argument('--region', default=default_region_name,
                       help=generate_help(region_help, default_region_name))
    group.add_argument('--dry-run', default=False, action='store_true',
                       help='Report on what would have happened. Take no mutable action.')
    if add_help:
        group.add_argument('-h', '--help', action='help',
                           help='Show this help message and exit')
    return group


def generate_help(message, default=None, use_default=True):
    if use_default:
        message = '{} Default: {}'.format(message, default)
    return message
