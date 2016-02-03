#!/usr/bin/python

# Define a stack to host a Consul cluster
#
# Template Parameters (provided at templat creation time):
# - name
#   Name of the stack, of course. Required.
# - description
#   Description of the stack. Please provide one.
# - vpc_id
#   ID of the VPC in which this stack is built
# - vpc_cidr
#   CIDR block of the vpc
# - subnet_ids
#   List of subnets in which the consul cluster should be built.
# - cluster_size
#   How many instances should participate in the cluster? Should be at least 3.
# - instance_type
#   Instance type of the instances. Defaults to t2.micro
#
# Stack Parameters (provided to the template at stack create/update time):
#
# - ConsulKey
#   Name of the key pair to use to connect to Consul cluster server instances
#
# Stack Outputs:
#

import troposphere.ec2 as ec2
import troposphere.iam as iam
import troposphere.autoscaling as asg
import troposphere as tp
from . import net
from . import asgtag, TemplateBuilderBase, AMI_REGION_MAP_NAME, REF_REGION

class ConsulTemplate(TemplateBuilderBase):

    CONSUL_KEY_PARAM_NAME = 'ConsulKey'

    def __init__(self, name,
                 vpc_id,
                 vpc_cidr,
                 subnet_ids,
                 description = '[REPLACEME]',
                 cluster_size = 3,
                 instance_type = 't2.micro'):
        super(ConsulTemplate, self).__init__(name, description)

        self.vpc_id = vpc_id
        self.vpc_cidr = vpc_cidr
        self.subnets = subnet_ids
        self.cluster_size = cluster_size
        self.instance_type = instance_type

        self.create_parameters()

        sg = self.create_sg()
        iam_profile = self.create_iam_profile()

        self.enis = [
            self.create_eni(i, sg, self.subnets[i % len(self.subnets)]) for i in range(0, cluster_size)
        ]
        self.asgs = [
            self.create_asg(i, sg, iam_profile, self.subnets[i % len(self.subnets)], self.enis[i]) for i in range(0, cluster_size)
        ]

    def create_parameters(self):
        self.add_parameter(tp.Parameter(self.CONSUL_KEY_PARAM_NAME, Type = 'String'))

    def create_eni(self, index, security_group, subnet_id):
        eni = ec2.NetworkInterface('ConsulENI{}'.format(index),
                                   Description = 'ENI for Consul cluster member {}'.format(index),
                                   GroupSet = [tp.Ref(security_group)],
                                   SourceDestCheck = True,
                                   SubnetId = subnet_id,
                                   Tags = self.default_tags)
        self.add_resource(eni)
        self.add_output(tp.Output(eni.name, Value = tp.Ref(eni)))
        return eni

    def create_sg(self):
        rules = [net.sg_rule(self.vpc_cidr, net.SSH, net.TCP)] + [
            net.sg_rule(self.vpc_cidr, ports, protocol)
            for protocol in [net.TCP, net.UDP] for ports in [53, (8300, 8302), 8400, 8500, 8600]
        ]
        sg = ec2.SecurityGroup('ConsulSecurityGroup',
                               GroupDescription = 'Consul Instance Security Group',
                               SecurityGroupIngress = rules,
                               VpcId = self.vpc_id,
                               Tags = self.default_tags)
        self.add_resource(sg)
        return sg
        
    def create_asg(self, index, security_group, iam_profile, subnet_id, eni):
        lc = asg.LaunchConfiguration('ConsulLC{}'.format(index),
                                     ImageId = tp.FindInMap(AMI_REGION_MAP_NAME, REF_REGION, 'GENERAL'),
                                     InstanceType = self.instance_type,
                                     SecurityGroups = [tp.Ref(security_group)],
                                     KeyName = tp.Ref(self.CONSUL_KEY_PARAM_NAME),
                                     IamInstanceProfile = tp.Ref(iam_profile),
                                     InstanceMonitoring = False,
                                     AssociatePublicIpAddress = False,
                                     UserData = self._create_consul_userdata(eni))
        group = asg.AutoScalingGroup('ConsulASG{}'.format(index),
                                     MinSize = 1, MaxSize = 1,
                                     LaunchConfigurationName = tp.Ref(lc),
                                     VPCZoneIdentifier = [subnet_id],
                                     Tags = asgtag(self._rename('{} Consul' + str(index))))
        self.add_resources(lc, group)
        return group


    def create_iam_profile(self):
        role = iam.Role('ConsulInstanceRole',
                        AssumeRolePolicyDocument = {
                            'Statement' : [ {
                                'Effect' : 'Allow',
                                'Principal' : { 'Service' : ['ec2.amazonaws.com'] },
                                'Action' : ['sts:AssumeRole']
                            } ]
                        },
                        Policies = [
                            iam.Policy(
                                PolicyName = 'ConsulInstance',
                                PolicyDocument = {
                                    'Statement' : [ {
                                        'Effect' : 'Allow',
                                        'Resource' : ['*'],
                                        'Action' : ['ec2:AttachNetworkInterface', 'ec2:DetachNetworkInterface']
                                    } ]
                                }
                            )
                        ])
        profile = iam.InstanceProfile('ConsulInstanceProfile',
                                      Path = '/',
                                      Roles = [tp.Ref(role)])
        self.add_resources(role, profile)
        return profile

    def _create_consul_userdata(self, eni):
        startup = [
            '#!/bin/bash\n',
            'yum update -y && yum install -y yum-cron && chkconfig yum-cron on\n',
            'REGION=$(curl http://169.254.169.254/latest/dynamic/instance-identity/document|grep region|awk -F\\" \'{print $4}\')\n',
            'INS_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)\n',
            'ENI_ID=', tp.Ref(eni), '\n',
            'aws ec2 attach-network-interface --instance-id $INS_ID --device-index 1 --network-interface-id $ENI_ID --region $REGION\n',
        ]
        return tp.Base64(tp.Join('', startup)) # TODO: There has GOT to be a better way to do userdata.
                            
if __name__ == '__main__':
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else 'Test'
    vpc_id = sys.argv[2] if len(sys.argv) > 2 else 'vpc-deadbeef'
    vpc_cidr = sys.argv[3] if len(sys.argv) > 3 else '10.0.0.0/16'
    subnet_ids = sys.argv[4:] if len(sys.argv) > 4 else ['subnet-deadbeef', 'subnet-cab4abba']

    print ConsulTemplate(name, vpc_id, vpc_cidr, subnet_ids).to_json()
