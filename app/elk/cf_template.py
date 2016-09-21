#
# Define a CloudFormation template to define an OpsWork stack that builds a tiny (all on one server) ELK stack
#
# Template Parameters (provided at template creation time):
# - name
#   Name of the stack, of course. Required
# - description
#   Description of the stack. Please provide one.
# - vpc_id
#   The ID of the VPC into which instances of the OpsWorks stack will be launched
# - default_public_subnet_id
#   The ID of the default subnet into which instances will be launched. For the Tiny stack, this should be a public
#   subnet so that public IPs can be assignet for Kibana.
# ---- Not sure what else we will need---
#
# Stack Parameters (provided at stack execution time):
# (none)
#
# Stack Outputs:
# (none)

import troposphere.iam as iam
import troposphere.opsworks as ow
import troposphere as tp

from scaffold.cf.template import TemplateBuilder
from scaffold.cf import assume_role_policy_document

class TinyELKTemplate(TemplateBuilder):

    BUILD_PARM_NAMES = ['default_subnet_id']
    INSTANCE_KEY_PARAM_NAME = 'ELKKey'

    def __init__(self, name,
                 description,
                 vpc_id,
                 default_subnet_id):
        super(TinyELKTemplate, self).__init__(name, description, TinyELKTemplate.BUILD_PARM_NAMES)

        self.vpc_id = vpc_id
        self.default_subnet_id = default_subnet_id

    def internal_add_mappings(self):
        # base template adds AMI mappings that we don't need
        pass
        
    def internal_build_template(self):
        self._create_stack()
        self._create_es_layer()

    def _create_stack(self):
        self.ow_stack = ow.Stack('{}OpsWorksStack'.format(self.name),
                                 DefaultInstanceProfileArn=tp.Ref(self._create_stack_instance_profile()),
                                 DefaultOs='Ubuntu 14.04 LTS',
                                 DefaultSubnetId=self.default_subnet_id,
                                 Name=self.name,
                                 ServiceRoleArn=tp.Ref(self._create_stack_service_role()),
                                 UseOpsworksSecurityGroups=False,
                                 VpcId=self.vpc_id
                                 )
        self.add_resource(self.ow_stack)

    def _create_es_layer(self):
        self.ow_layer = ow.Layer('{}ElasticSearchLayer'.format(self.name),
                                 AutoAssignElasticIps=False,
                                 AutoAssignPublicIps=False,
                                 EnableAutoHealing=True,
                                 Name=self.name,
                                 Shortname=self.name,
                                 StackId=tp.Ref(self.ow_stack),
                                 Type='custom')
        self.add_resource(self.ow_layer)
                                 
                                 

    def _create_stack_instance_profile(self):
        base_name = '{}OpsWorksInstance'.format(self.name)
        role = iam.Role('{}Role'.format(base_name),
                        AssumeRolePolicyDocument=assume_role_policy_document.ec2,
                        Policies=[
                            iam.Policy(
                                PolicyName=base_name,
                                PolicyDocument={
                                    'Statement':[{
                                        'Effect': 'Allow',
                                        'Resource': ['*'],  # TODO: replace with bucket name
                                        'Action': ['s3:Get*']
                                    }]
                                }
                            )
                        ])
        profile = iam.InstanceProfile('{}Profile'.format(base_name),
                                      Path='/',
                                      Roles=[tp.Ref(role)])
        self.add_resources(role, profile)
        return profile

    def _create_stack_service_role(self):
        policy_name = '{}OpsWorksService'.format(self.name)
        role = iam.Role('{}Role'.format(policy_name),
                        AssumeRolePolicyDocument=assume_role_policy_document.opsworks,
                        Policies=[
                            iam.Policy(
                                PolicyName=policy_name,
                                PolicyDocument={
                                    "Statement": [{
                                        "Effect": "Allow",
                                        "Resource": ["*"],
                                        "Action": ["ec2:*",
                                                   "iam:PassRole",
                                                   "cloudwatch:GetMetricStatistics", "cloudwatch:DescribeAlarms",
                                                   "ecs:*",
                                                   "elasticloadbalancing:*",
                                                   "rds:*"
                                        ]
                                    }]
                                }
                            )
                        ])
        self.add_resource(role)
        return role
    

if __name__ == '__main__':
    template = TinyELKTemplate('TestTinyELK', 'Testing', 'vpc-deadbeef', 'subnet-cab4abba')
    template.build_template()
    print template.to_json()
