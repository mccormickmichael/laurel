import json
import os.path
import troposphere.cloudtrail as ct
import troposphere.iam as iam
import troposphere.s3 as s3
import troposphere as tp

from scaffold.template import TemplateBuilder
from . import discover_policy_files, load_policy_file


class IAMTemplate(TemplateBuilder):

    BUILD_PARM_NAMES = ['s3_bucket_name', 's3_path_prefix', 'logging_enabled']

    OUTPUT_NAME_BUCKET = 'CloudTrailBucket'
    OUTPUT_NAME_TRAIL = 'Trail'

    POLICY_DIR_NAME = 'policies'
    USER_FILE_NAME = 'users.yml'
    GROUP_FILE_NAME = 'groups.yml'
    ROLE_FILE_NAME = 'roles.yml'

    def __init__(self, name,
                 s3_bucket_name,
                 s3_path_prefix='',
                 iam_doc_dir='.',
                 description='[REPLACE ME]',
                 logging_enabled=False):
        super(IAMTemplate, self).__init__(name, description, IAMTemplate.BUILD_PARM_NAMES)
        self.s3_bucket_name = s3_bucket_name
        self.s3_path_prefix = s3_path_prefix
        self.iam_doc_dir = iam_doc_dir
        self.logging_enabled = logging_enabled

    def internal_add_mappings(self):
        pass

    def internal_build_template(self):
        self._create_cloudtrail_bucket()
        self._create_cloudtrail()
        self._create_policies()

    def _create_policies(self):
        policy_file_mapping = discover_policy_files(self._policy_dir())
        for policy_name, policy_file in policy_file_mapping.items():
            policy_doc = load_policy_file(policy_file)
            policy = iam.ManagedPolicy(policy_name,
                                       PolicyDocument=policy_doc)
            self.add_resource(policy)
            self.output_ref(IAMTemplate._policy_res_name(policy_name), policy)

    def _create_cloudtrail_bucket(self):
        lc = s3.LifecycleConfiguration(Rules=[s3.LifecycleRule(ExpirationInDays=30,
                                                               Prefix=self.s3_path_prefix,
                                                               Status='Enabled')
                                              ])
        bucket = s3.Bucket(self.OUTPUT_NAME_BUCKET,
                           BucketName=self.s3_bucket_name,
                           LifecycleConfiguration=lc,
                           # DeletionPolicy='Retain',
                           Tags=self.default_tags)

        policy = s3.BucketPolicy(IAMTemplate._policy_res_name(self.OUTPUT_NAME_BUCKET),
                                 Bucket=tp.Ref(bucket),
                                 PolicyDocument=self._create_bucket_policy(),
                                 DependsOn=bucket.title)

        self.add_resources(bucket, policy)
        self.output(bucket)
        self.bucket = bucket
        self.bucket_policy = policy

    def _create_cloudtrail(self):
        trail = ct.Trail(self.OUTPUT_NAME_TRAIL,
                         S3BucketName=self.s3_bucket_name,
                         S3KeyPrefix=self.s3_path_prefix,
                         IsLogging=self.logging_enabled,
                         Tags=self.default_tags,
                         DependsOn=self.bucket_policy.title)
        self.add_resource(trail)
        self.output(trail)
        self.trail = trail

    def _create_bucket_policy(self):
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AWSCloudTrailAclCheck20150319",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudtrail.amazonaws.com"
                    },
                    "Action": "s3:GetBucketAcl",
                    "Resource": "arn:aws:s3:::{}".format(self.s3_bucket_name)
                },
                {
                    "Sid": "AWSCloudTrailWrite20150319",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudtrail.amazonaws.com"
                    },
                    "Action": "s3:PutObject",
                    "Resource": "arn:aws:s3:::{}/*".format(self.s3_bucket_name),
                    "Condition": {
                        "StringEquals": {
                            "s3:x-amz-acl": "bucket-owner-full-control"
                        }
                    }
                }
            ]
        }

    @staticmethod
    def _policy_res_name(policy_name):
        return policy_name + 'Policy'

    def _policy_dir(self):
        return os.path.join(self.iam_doc_dir, IAMTemplate.POLICY_DIR_NAME)

if __name__ == '__main__':
    template = IAMTemplate('testing', 'test-bucket')
    template.build_template()
    print template.to_json()
