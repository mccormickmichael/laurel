#!/usr/bin/python

# Define a NAT ASG and a Bastion ASG. Depends on a network stack to be defined.
# TODO: template parameters
# TODO: stack parameters
# TODO: stack outputs

import sys
import troposphere.ec2 as ec2
import troposphere.iam as iam
import troposphere.autoscaling as asg
import troposphere as tp
from . import vpc # TODO TemplateBuilderBase should be in __init__
from . import asgtag

class ServicesTemplate(vpc.TemplateBuilderBase):

    BASTION_KEY_PARM_NAME = 'BastionKey'

    def __init__(self, name, 
                 vpc_id,
                 vpc_cidr,
                 private_route_table_id,
                 public_subnet_ids,
                 description = '[REPLACEME]',
                 region = 'us-west-2',
                 nat_instance_type = 't2.micro',
                 bastion_instance_type = 't2.micro'):
        super(ServicesTemplate, self).__init__(name, description)

        self.vpc_id = vpc_id
        self.vpc_cidr = vpc_cidr
        self.subnet_ids = public_subnet_ids
        self.route_table_id = private_route_table_id
        self.region = region
        self.nat_instance_type = nat_instance_type
        self.bastion_instance_type = bastion_instance_type

        self.create_parameters()

        self.create_nat()
        self.create_bastion()

    def create_parameters(self):
        self.add_parameter(tp.Parameter(self.BASTION_KEY_PARM_NAME, Type = 'String'))

    def create_nat(self):
        nat_sg = self.create_nat_sg()
        nat_asg = self.create_nat_asg(nat_sg)

    def create_bastion(self):
        bastion_sg = self.create_bastion_sg()
        bastion_asg = self.create_bastion_asg(bastion_sg)

    def create_nat_asg(self, sg):
        profile = self.create_nat_iam_profile()
        lc = asg.LaunchConfiguration('NATLC',
                                     ImageId = tp.FindInMap(vpc.AMI_REGION_MAP_NAME, vpc.REF_REGION, 'NAT'),
                                     InstanceType = self.nat_instance_type,
                                     SecurityGroups = [tp.Ref(sg)],
                                     KeyName = tp.Ref(self.BASTION_KEY_PARM_NAME),
                                     IamInstanceProfile = tp.Ref(profile),
                                     InstanceMonitoring = False,
                                     AssociatePublicIpAddress = True,
                                     UserData = self._create_nat_userdata())
        group = asg.AutoScalingGroup('NATASG',
                                     MinSize = 1, MaxSize = 1,
                                     LaunchConfigurationName = tp.Ref(lc),
                                     VPCZoneIdentifier = self.subnet_ids,
                                     Tags = asgtag(self._rename('{} NAT')))
        # TODO: Copy ALL default tags to AutoScalingTags
        self.add_resources([group, lc])
        return group

    def create_nat_iam_profile(self):
        role = iam.Role('NATInstanceRole',
                           AssumeRolePolicyDocument = {
                               'Statement' : [ {
                                   'Effect' : 'Allow',
                                   'Principal' : { 'Service' : ['ec2.amazonaws.com'] },
                                   'Action' : ['sts:AssumeRole']
                               } ]
                           },
                           Policies = [
                               iam.Policy(
                                   PolicyName = 'NATInstance',
                                   PolicyDocument = {
                                       'Statement' : [ {
                                           'Effect' : 'Allow',
                                           'Resource' : ['*'],
                                           'Action' : ['ec2:CreateRoute', 'ec2:DeleteRoute']
                                       } ]
                                   }
                               )
                           ])
        profile = iam.InstanceProfile('NATInstanceProfile',
                                      Path = '/',
                                      Roles = [tp.Ref(role)])
        self.add_resources([role, profile])
        return profile

    def _create_nat_userdata(self):
        startup = [
            "#!/bin/bash",
            "yum update -y && yum install -y yum-cron && chkconfig yum-cron on",
            "INS_ID=`curl http://169.254.169.254/latest/meta-data/instance-id`",
            "aws ec2 delete-route --destination-cidr-block 0.0.0.0/0 --route-table-id {} --region {}".format(self.route_table_id, self.region),
            "aws ec2 create-route --route-table-id {} --destination-cidr-block 0.0.0.0/0 --instance-id $INS_ID --region {}".format(self.route_table_id, self.region)
        ]
        return tp.Base64(tp.Join('\n', startup))

    def create_bastion_asg(self, sg):
        lc = asg.LaunchConfiguration('BastionLC',
                                     ImageId = tp.FindInMap(vpc.AMI_REGION_MAP_NAME, vpc.REF_REGION, 'BASTION'),
                                     InstanceType = self.bastion_instance_type,
                                     SecurityGroups = [tp.Ref(sg)],
                                     KeyName = tp.Ref(self.BASTION_KEY_PARM_NAME),
                                     InstanceMonitoring = False,
                                     AssociatePublicIpAddress = True,
                                     UserData = self._create_bastion_userdata())
        group = asg.AutoScalingGroup('BastionASG',
                                     MinSize = 1, MaxSize = 1,
                                     LaunchConfigurationName = tp.Ref(lc),
                                     VPCZoneIdentifier = self.subnet_ids,
                                     Tags = asgtag(self._rename('{} Bastion')))
        self.add_resources([group, lc])
        return asg

    def _create_bastion_userdata(self):
        startup = [
            '#!/bin/bash',
            'yum update -y && yum install -y yum-cron && chkconfig yum-cron on'
        ]
        return tp.Base64(tp.Join('\n', startup))

    def create_nat_sg(self):
        sg = ec2.SecurityGroup('NATSecurityGroup',
                               GroupDescription = 'NAT Instance Security Group',
                               SecurityGroupIngress = vpc.SecurityGroupRuleBuilder(self.vpc_cidr).any().rules(),
                               VpcId = self.vpc_id,
                               Tags = self.default_tags)
        self.add_resource(sg)
        return sg

    def create_bastion_sg(self):
        sg = ec2.SecurityGroup('BastionSecurityGroup',
                               GroupDescription = 'Bastion Instance Security Group',
                               SecurityGroupIngress = vpc.SecurityGroupRuleBuilder(vpc.CIDR_ANY).ssh().rules(),
                               VpcId = self.vpc_id,
                               Tags = self.default_tags)
        self.add_resource(sg)
        return sg

if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'Test'
    vpc_id = sys.argv[2] if len(sys.argv) > 2 else 'vpc-deadbeef'
    vpc_cidr = sys.argv[3] if len(sys.argv) > 3 else '10.0.0.0/8'
    route_table = sys.argv[4] if len(sys.argv) > 4 else 'rtb-deadbeef'
    subnets = sys.argv[5:] if len(sys.argv) > 5 else ['subnet-deadbeef', 'subnet-cab4abba']
    print ServicesTemplate(name, vpc_id, vpc_cidr, route_table, subnets).to_json()
