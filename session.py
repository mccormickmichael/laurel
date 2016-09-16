import logging

import boto3

logger = logging.getLogger('laurel.session')


def new(profile_name, region_name, role_name):
    session = boto3.session.Session(profile_name=profile_name, region_name=region_name)
    if not role_name:
        return session

    iam = session.resource('iam')
    sts = session.client('sts')
    target_role = iam.Role(role_name)
    user_name = iam.CurrentUser().user_name

    response = sts.assume_role(RoleArn=target_role.arn,
                               RoleSessionName='{}+{}'.format(user_name, target_role.name))
    creds = response['Credentials']
    assumed_role = response['AssumedRoleUser']

    logger.info('User %s is assuming role_name %s', user_name, assumed_role['Arn'])

    return boto3.session.Session(aws_access_key_id=creds['AccessKeyId'],
                                 aws_secret_access_key=creds['SecretAccessKey'],
                                 aws_session_token=creds['SessionToken'],
                                 region_name=region_name)
