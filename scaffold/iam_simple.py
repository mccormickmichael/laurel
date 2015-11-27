#!/usr/bin/python

# Creates a Cloudformation Template for IAM instance profiles to be used by supporting applications

import sys

from awacs.aws import Action, Allow, Policy, Principal, Statement
from awacs.iam import ARN as IAM_ARN
from awacs.s3 import ARN as S3_ARN
from awacs.sts import AssumeRole as STSAssumeRole
from troposphere import Output, Parameter, Ref, Template
from troposphere import AWS_ACCOUNT_ID
from troposphere.iam import InstanceProfile, ManagedPolicy, Role

class IAM(object):
    def __init__(self, name, description = 'IAM policies and roles for supporting application stacks'):
        self.name = name

        t = Template()
        t.add_version()
        t.add_description(description)

        t.add_resource(self._create_bastion_profile())
        t.add_output(self._create_outputs())

        self.t = t

    def to_json(self):
        return self.t.to_json()

    def _create_bastion_profile(self):

        s3_all_policy_doc = Policy(
            Version = '2012-10-17',
            Statement = [ Statement(
                Effect = Allow,
                Action = [Action('s3', '*')],
                Resource = [S3_ARN('*')],
            )])
        ec2_assume_role_policy_doc = Policy(
            Version = '2012-10-17',
            Statement = [ Statement(
                Effect = Allow,
                Principal = Principal('Service', ['ec2.amazonaws.com']),
                Action = [STSAssumeRole]
            )])
        s3_all_managed_policy = ManagedPolicy('S3AllPolicy',
                                               Description = 'S3 All Policy',
                                               Path = '/',
                                               PolicyDocument = s3_all_policy_doc)

        bastion_role = Role('BastionRole',
                            AssumeRolePolicyDocument = ec2_assume_role_policy_doc,
                            ManagedPolicyArns = [Ref(s3_all_managed_policy)])

        self.bastion_profile = InstanceProfile('BastionInstanceProfile',
                                               Roles = [Ref(bastion_role)])

        return [s3_all_managed_policy, bastion_role, self.bastion_profile]

    def _create_outputs(self):
        return [
            Output('BastionInstanceProfile', Value = Ref(self.bastion_profile))
        ]

if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'SimpleIAM'
    print IAM(name).to_json()
