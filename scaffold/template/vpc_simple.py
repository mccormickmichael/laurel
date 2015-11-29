#!/usr/bin/python

# Creates a CloudFormation Template for a simple VPC:
# - One Public Subnet
# - One Private Subnet
# - One NAT that doubles as a bastion server
#
# Allowed traffic from public to private subnet: SSH through the bastion server
# Allowed traffic from private subnet to internet: HTTP, HTTPS, SSH
#
# Parameters:
# Name: The name of the VPC and associated subnets
# BastionKey: the public key name to be used to access the bastion server.
# VpcCidr: CIDR block of the VPC. Defaults to 172.16.0.0/16
# PublicSubnetCidr: CIDR block of the public subnet. Defaults to 172.16.0.0/24
# PrivateSubnetCidr: CIDR block of the private subnet. Defaults to 172.16.1.0/24
#
# Stack Outputs:
# NATIP:         The public IP of the NAT server
# BastionIP:     The public IP of the bastion server
# PublicSubnet:  The ID of the public subnet
# PrivateSubnet: The ID of the private subnet

import sys
from troposphere import (Base64, FindInMap, GetAtt, GetAZs, Join, Output, Parameter, Ref,
                         Select, Tags, Template)
from troposphere.ec2 import (Instance, InternetGateway, NetworkAcl, NetworkAclEntry,
                             NetworkInterfaceProperty, PortRange, Route, RouteTable,
                             SecurityGroup, SecurityGroupRule, Subnet,
                             SubnetNetworkAclAssociation, SubnetRouteTableAssociation,
                             VPC, VPCGatewayAttachment)
from . import utils, vpc
from .vpc import NaclBuilder, SecurityGroupRuleBuilder

class SimpleVPC(object):

    PARM_KEY_NAME = 'KeyNameParameter'
    PARM_VPC_CIDR = 'VpcCidrParameter'
    PARM_PUB_CIDR = 'PublicSubnetCidrParameter'
    PARM_PRIV_CIDR = 'PrivateSubnetCidrParameter'

    DEFAULT_PARM_VPC_CIDR = '172.16.0.0/16'
    DEFAULT_PARM_PUB_CIDR = '172.16.0.0/24'
    DEFAULT_PARM_PRIV_CIDR = '172.16.1.0/24'

    AMI_REGION_MAP = 'AMIRegionMap'

    def __init__(self, name, description = 'Simple VPC: 1 public subnet, 1 private subnet'):
        self.name = name
        self.stack_name_ref = Ref('AWS::StackName')
        self.region_ref = Ref('AWS::Region')
        self.default_tags = Tags(Application = self.stack_name_ref, Name = self.name)
        
        t = Template()
        t.add_version()

        t.add_description(description)
        t.add_parameter(self._create_parameters())
        
        t.add_mapping(self.AMI_REGION_MAP, self._create_ami_mapping())
        
        t.add_resource(self._create_vpc_with_gateway())
        t.add_resource(self._create_public_subnet())
        t.add_resource(self._create_nat())
        t.add_resource(self._create_bastion())
        t.add_resource(self._create_private_subnet())
        
        t.add_output(self._create_outputs())

        self.t = t

    def to_json(self):
        return self.t.to_json()
        
    def _create_parameters(self):
        return [
            Parameter(
                self.PARM_KEY_NAME,
                Description = "Name of existing key pair to allow access to the bastion server",
                Type = "String"
            ),
            Parameter(
                self.PARM_VPC_CIDR,
                Description = 'CIDR block of the VPC',
                Type = 'String',
                Default = self.DEFAULT_PARM_VPC_CIDR
                # TODO: formatting constraints?
            ),
            Parameter(
                self.PARM_PUB_CIDR,
                Description = 'CIDR block of the public subnet',
                Type = 'String',
                Default = self.DEFAULT_PARM_PUB_CIDR
            ),
            Parameter(
                self.PARM_PRIV_CIDR,
                Description = 'CIDR block of the private subnet',
                Type = 'String',
                Default = self.DEFAULT_PARM_PRIV_CIDR
            )]

    def _create_ami_mapping(self):
        return {
            'us-east-1' : { 'NAT' : 'ami-303b1458', 'BASTION': 'ami-60b6c60a' },
            'us-west-1' : { 'NAT' : 'ami-7da94839', 'BASTION': 'ami-d5ea86b5' },
            'us-west-2' : { 'NAT' : 'ami-69ae8259', 'BASTION': 'ami-f0091d91' }
            #'eu-west-1'
            #'eu-west-2'
            #'eu-central-1'
            #'sa-east-1'
            #'ap-southeast-1'
            #'ap-southeast-2' 
            #'ap-northeast-1' 
        }
        
    def _create_vpc_with_gateway(self):
        resources = vpc.create_vpc_with_inet_gateway(self.name, self.PARM_VPC_CIDR, self.default_tags)
        self.vpc = resources['VPC']
        self.igw = resources['InternetGateway']
        self.igw_attach = resources['GatewayAttachment']
        return resources.values()

    def _create_public_subnet(self):
        name_public = '{0}Public'.format(self.name)
        tags = utils.merge_tags(self.default_tags, Tags(Name = name_public))
        self.pub_subnet = Subnet('{0}Subnet'.format(name_public),
                                 AvailabilityZone = Select(0, GetAZs()),
                                 CidrBlock = Ref(self.PARM_PUB_CIDR),
                                 MapPublicIpOnLaunch = True,
                                 VpcId = Ref(self.vpc),
                                 Tags = tags)
        self.pub_rt = RouteTable('{0}RT'.format(name_public),
                                 VpcId = Ref(self.vpc),
                                 Tags = tags)
        self.pub_nacl = NetworkAcl('{0}Nacl'.format(name_public),
                                   VpcId = Ref(self.vpc),
                                   Tags = tags)
        nacl_assoc = SubnetNetworkAclAssociation(
            '{0}{1}'.format(self.pub_subnet.name, self.pub_nacl.name),
            SubnetId = Ref(self.pub_subnet),
            NetworkAclId = Ref(self.pub_nacl))
        rt_assoc = SubnetRouteTableAssociation(
            '{0}{1}'.format(self.pub_subnet.name, self.pub_rt.name),
            SubnetId = Ref(self.pub_subnet),
            RouteTableId = Ref(self.pub_rt))
        igw_route = Route(
            '{0}Route'.format(name_public),
            RouteTableId = Ref(self.pub_rt),
            DependsOn = self.igw_attach.name,
            GatewayId = Ref(self.igw),
            DestinationCidrBlock = vpc.CIDR_ANY)
        
        nb = NaclBuilder(self.pub_nacl)
        nb.ingress().allow().http().https().ssh().ephemeral()
        nb.egress().allow().http().https().ephemeral().ssh(Ref(self.PARM_PRIV_CIDR))

        return [self.pub_subnet, self.pub_rt, self.pub_nacl, nacl_assoc, rt_assoc, igw_route] + nb.resources()

    def _create_nat(self):
        sg_ingress = SecurityGroupRuleBuilder(Ref(self.PARM_PRIV_CIDR)).http().https().ssh(Ref(self.PARM_PUB_CIDR))
        sg_egress = SecurityGroupRuleBuilder(vpc.CIDR_ANY).http().https()
        self.nat_sg = SecurityGroup('{0}NATSG'.format(self.name),
                                    VpcId = Ref(self.vpc),
                                    GroupDescription = 'NAT Security Group',
                                    SecurityGroupEgress = sg_egress.rules(),
                                    SecurityGroupIngress = sg_ingress.rules(),
                                    Tags = self.default_tags)
        imageid = FindInMap(self.AMI_REGION_MAP, self.region_ref, 'NAT')
        resources = vpc.create_nat_instance(self.name, self.nat_sg, self.pub_subnet, self.PARM_KEY_NAME, imageid, self.default_tags, [self.igw_attach])
        self.nat = resources['Instance']
        return [self.nat_sg, self.nat]

    def _create_bastion(self):
        sg_ingress = SecurityGroupRuleBuilder(vpc.CIDR_ANY).ssh()
        sg_egress = SecurityGroupRuleBuilder().ssh(Ref(self.PARM_VPC_CIDR))
        self.bastion_sg = SecurityGroup('{0}BastionSG'.format(self.name),
                                        VpcId = Ref(self.vpc),
                                        GroupDescription = 'Bastion Security Group',
                                        SecurityGroupEgress = sg_egress.rules(),
                                        SecurityGroupIngress = sg_ingress.rules(),
                                        Tags = self.default_tags)
        imageid = FindInMap(self.AMI_REGION_MAP, self.region_ref, 'BASTION')
        resources = vpc.create_bastion_instance(self.name, self.bastion_sg, self.pub_subnet, self.PARM_KEY_NAME, imageid, self.default_tags, [self.igw_attach])
        self.bastion = resources['Instance']
        return [self.bastion_sg, self.bastion]

    def _create_private_subnet(self):
        name_private = self._fname('{0}Private')
        tags = utils.merge_tags(self.default_tags, Tags(Name = name_private))
        pub_cidr_ref = Ref(self.PARM_PUB_CIDR)
        self.priv_subnet = Subnet('{0}Subnet'.format(name_private),
                                  AvailabilityZone = Select(1, GetAZs()),
                                  CidrBlock = Ref(self.PARM_PRIV_CIDR),
                                  MapPublicIpOnLaunch = False,
                                  VpcId = Ref(self.vpc),
                                  Tags = tags)
        self.priv_rt = RouteTable('{0}RT'.format(name_private),
                                  VpcId = Ref(self.vpc),
                                  Tags = tags)
        self.priv_nacl = NetworkAcl('{0}Nacl'.format(name_private),
                                    VpcId = Ref(self.vpc),
                                    Tags = tags)
        nacl_assoc = SubnetNetworkAclAssociation('{0}{1}'.format(self.priv_subnet.name, self.priv_nacl.name),
                                                 SubnetId = Ref(self.priv_subnet),
                                                 NetworkAclId = Ref(self.priv_nacl))
        rt_assoc = SubnetRouteTableAssociation('{0}{1}'.format(self.priv_subnet.name, self.priv_rt.name),
                                               SubnetId = Ref(self.priv_subnet),
                                               RouteTableId = Ref(self.priv_rt))
        nat_route = Route('{0}Route'.format(name_private),
                          RouteTableId = Ref(self.priv_rt),
                          DependsOn = self.nat.name,
                          InstanceId = Ref(self.nat),
                          DestinationCidrBlock = vpc.CIDR_ANY)

        nb = NaclBuilder(self.priv_nacl)
        nb.ingress().allow().ssh(pub_cidr_ref).ephemeral()
        nb.egress().allow().http().https().ephemeral(pub_cidr_ref)

        return [self.priv_subnet, self.priv_rt, self.priv_nacl, nacl_assoc, rt_assoc, nat_route] + nb.resources()

    def _create_outputs(self):
        return [
            Output('PublicSubnet', Value = Ref(self.pub_subnet)),
            Output('PrivateSubnet', Value = Ref(self.priv_subnet)),
            Output('NATIP', Value = GetAtt(self.nat, 'PublicIp')),
            Output('BastionIP', Value = GetAtt(self.bastion, 'PublicIp'))
            ]

    def _fname(self, fmt):
        return fmt.format(self.name)

if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'Simple'
    print SimpleVPC(name).to_json()
