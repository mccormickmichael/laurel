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
# BastionKey: the public key name to be used to access the bastion server.
# VpcCidr: CIDR block of the VPC. Defaults to 172.16.0.0/16
# PublicSubnetCidr: CIDR block of the public subnet. Defaults to 172.16.0.0/24
# PrivateSubnetCidr: CIDR block of the private subnet. Defaults to 172.16.1.0/24
#
# Stack Outputs:
# BastionIP:     The public IP of the bastion server
# PublicSubnet:  The ID of the public subnet
# PrivateSubnet: The ID of the private subnet

import sys
from troposphere import FindInMap, GetAtt, Output, Parameter, Ref, Tags, Template
from troposphere.ec2 import Instance, NetworkAcl, SecurityGroup
from . import utils, vpc, cidr
from .vpc import NaclBuilder, SecurityGroupRuleBuilder, TemplateBuilderBase

class SimpleVPC(TemplateBuilderBase):

    PARM_KEY_NAME = 'KeyNameParameter'
    PARM_VPC_CIDR = 'VpcCidrParameter'
    PARM_PUB_CIDR = 'PublicSubnetCidrParameter'
    PARM_PRIV_CIDR = 'PrivateSubnetCidrParameter'

    DEFAULT_PARM_VPC_CIDR = '172.16.0.0/16'
    DEFAULT_PARM_PUB_CIDR = '172.16.0.0/24'
    DEFAULT_PARM_PRIV_CIDR = '172.16.1.0/24'

    def __init__(self, name, description = 'Simple VPC: 1 public subnet, 1 private subnet'):
        super(SimpleVPC, self).__init__(name, description)
        
        self.add_parameters(self._create_parameters())
        self.add_resource(self._create_vpc_with_gateway())
        self.add_resource(self._create_public_subnet())
        self.add_resource(self._create_nat())
        self.add_resource(self._create_bastion())
        self.add_resource(self._create_private_subnet())
        
        self.add_output(self._create_outputs())
        
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

    def _create_vpc_with_gateway(self):
        resources = vpc.create_vpc_with_inet_gateway(self.name, self.PARM_VPC_CIDR, self.default_tags)
        self.vpc = resources['VPC']
        self.igw = resources['InternetGateway']
        self.igw_attach = resources['GatewayAttachment']
        return resources.values()

    def _create_public_subnet(self):
        resources = vpc.create_public_subnet(self.name, 0, self.PARM_PUB_CIDR, self.vpc, self.igw, self.default_tags)
        
        nb = NaclBuilder(resources['NetworkAcl'])
        nb.ingress().allow().http().https().ssh().ephemeral()
        nb.egress().allow().http().https().ephemeral().ssh(Ref(self.PARM_PRIV_CIDR))
        self.pub_subnet = resources['Subnet']

        return resources.values() + nb.resources()

    def _create_nat(self):
        sg_ingress = SecurityGroupRuleBuilder(Ref(self.PARM_PRIV_CIDR)).http().https().ssh(Ref(self.PARM_PUB_CIDR))
        sg_egress = SecurityGroupRuleBuilder(vpc.CIDR_ANY).http().https()
        self.nat_sg = SecurityGroup('{0}NATSG'.format(self.name),
                                    VpcId = Ref(self.vpc),
                                    GroupDescription = 'NAT Security Group',
                                    SecurityGroupEgress = sg_egress.rules(),
                                    SecurityGroupIngress = sg_ingress.rules(),
                                    Tags = self.default_tags)
        imageid = FindInMap(vpc.AMI_REGION_MAP_NAME, vpc.REF_REGION, 'NAT')
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
        imageid = FindInMap(vpc.AMI_REGION_MAP_NAME, vpc.REF_REGION, 'BASTION')
        resources = vpc.create_bastion_instance(self.name, self.bastion_sg, self.pub_subnet, self.PARM_KEY_NAME, imageid, self.default_tags, [self.igw_attach])
        self.bastion = resources['Instance']
        return [self.bastion_sg, self.bastion]

    def _create_private_subnet(self):
        resources = vpc.create_private_subnet(self.name, 1, self.PARM_PRIV_CIDR, self.vpc, self.nat, self.default_tags)

        self.priv_subnet = resources['Subnet']
        self.priv_rt = resources['RouteTable']
        self.priv_nacl = resources['NetworkAcl']

        pub_cidr_ref = Ref(self.PARM_PUB_CIDR)
        nb = NaclBuilder(self.priv_nacl)
        nb.ingress().allow().ssh(pub_cidr_ref).ephemeral()
        nb.egress().allow().http().https().ephemeral(pub_cidr_ref)

        return resources.values() + nb.resources()

    def _create_outputs(self):
        return [
            Output('PublicSubnet', Value = Ref(self.pub_subnet)),
            Output('PrivateSubnet', Value = Ref(self.priv_subnet)),
            Output('BastionIP', Value = GetAtt(self.bastion, 'PublicIp'))
            ]

    def _fname(self, fmt):
        return fmt.format(self.name)

if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'Simple'
    print SimpleVPC(name).to_json()
