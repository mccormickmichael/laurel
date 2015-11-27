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
# BastionIP: The public IP of the bastion server

import sys

from troposphere import Base64, FindInMap, GetAtt, GetAZs, Join, Output, Parameter, Ref, Select, Tags, Template
from troposphere.ec2 import Instance, InternetGateway, NetworkAcl, NetworkAclEntry, NetworkInterfaceProperty, PortRange, Route, RouteTable, SecurityGroup, SecurityGroupRule, Subnet, SubnetNetworkAclAssociation, SubnetRouteTableAssociation, VPC, VPCGatewayAttachment

CIDR_ANY = '0.0.0.0/0'

class ProtocolBuilder(object):
    def __init__(self, parent, cidr = None):
        self.parent = parent
        self.cidr = cidr

    def http(self, cidr = None):
        return self.tcp('Http', 80, 80, cidr)
    
    def https(self, cidr = None):
        return self.tcp('Https', 443, 443, cidr)
    
    def ssh(self, cidr = None):
        return self.tcp('SSH', 22, 22, cidr)
    
    def ephemeral(self, cidr = None):
        return self.tcp('EphemeralReturn', 49152, 65535, cidr)

    def tcp(self, name, port_from, port_to, cidr = None):
        cidr = cidr or self.cidr
        self.parent._addrule(name, self.action(), '6', port_from, port_to, cidr)
        return self

class AllowProtocolBuilder(ProtocolBuilder):
    def __init__(self, parent, cidr = None):
        super(AllowProtocolBuilder, self).__init__(parent, cidr)

    def action(self):
        return 'allow'

class DenyProtocolBuilder(ProtocolBuilder):
    def __init__(self, parent, cidr = None):
        super(DenyProtocolBuilder, self).__init__(parent, cidr)

    def action(self):
        return 'deny'
        
class NaclEntryBuilder(object):
    def __init__(self, parent):
        self.parent = parent
        self.rule = 100
        
    def deny(self, cidr = None):
        return DenyProtocolBuilder(self, cidr)
        
    def allow(self, cidr = None):
        return AllowProtocolBuilder(self, cidr)

    def _addrule(self, name, action, protocol, port_from, port_to, cidr = None):
        self.parent._addrule(self._rulename(name), self._nextrulenum(), protocol, port_from, port_to, self._egress(), action, cidr)

    def _nextrulenum(self):
        rule = self.rule
        self.rule += 1
        return rule

class NaclIngressBuilder(NaclEntryBuilder):
    def __init__(self, parent):
        super(NaclIngressBuilder, self).__init__(parent)
        
    def _rulename(self, prefix):
        return '{0}In'.format(prefix)

    def _egress(self):
        return 'false'

class NaclEgressBuilder(NaclEntryBuilder):
    def __init__(self, parent):
        super(NaclEgressBuilder, self).__init__(parent)

    def _rulename(self, prefix):
        return '{0}Out'.format(prefix)

    def _egress(self):
        return 'true'

class NaclBuilder(object):
    def __init__(self, nacl, cidr = CIDR_ANY):
        self.nacl = nacl
        self.cidr = cidr
        self.ib = NaclIngressBuilder(self)
        self.eb = NaclEgressBuilder(self)
        self.entries = []

    def ingress(self):
        return self.ib
    
    def egress(self):
        return self.eb
    
    def resources(self):
        return self.entries
    
    def _addrule(self, name, number, protocol, from_port, to_port, egress, action, cidr = None):
        cidr = cidr or self.cidr
        rule = NetworkAclEntry('{0}{1}'.format(self.nacl.name, name),
                               NetworkAclId = Ref(self.nacl),
                               RuleNumber = str(number),
                               Protocol = protocol,
                               PortRange = PortRange(From = from_port, To = to_port),
                               Egress = egress,
                               RuleAction = action,
                               CidrBlock = cidr)
        self.entries.append(rule)
        
class SecurityGroupRuleBuilder(ProtocolBuilder):
    def __init__(self, cidr = CIDR_ANY):
        super(SecurityGroupRuleBuilder, self).__init__(self, cidr)
        self._rules = []

    def rules(self):
        return self._rules

    def action(self):
        return ''
    
    def _addrule(self, name_ignored, action_ignored, protocol, port_from, port_to, cidr):
        self._rules.append(SecurityGroupRule(
            CidrIp = cidr,
            FromPort = port_from,
            ToPort = port_to,
            IpProtocol = protocol))

class SimpleVPC(object):

    PARM_KEY_NAME = 'KeyNameParameter'
    PARM_VPC_CIDR = 'VpcCidrParameter'
    PARM_PUB_CIDR = 'PublicSubnetCidrParameter'
    PARM_PRIV_CIDR = 'PrivateSubnetCidrParameter'

    DEFAULT_PARM_VPC_CIDR = '172.16.0.0/16'
    DEFAULT_PARM_PUB_CIDR = '172.16.0.0/24'
    DEFAULT_PARM_PRIV_CIDR = '172.16.1.0/24'

    NAT_AMI_REGION_MAP = 'NatAMIRegionMap'

    def __init__(self, name, description = 'Simple VPC: 1 public subnet, 1 private subnet'):
        self.name = name
        self.stack_name_ref = Ref('AWS::StackName')
        self.region_ref = Ref('AWS::Region')
        self.default_tags = Tags(Application = self.stack_name_ref, Name = self.name)
        
        t = Template()
        t.add_version()

        t.add_description(description)
        t.add_parameter(self._create_parameters())
        
        t.add_mapping(self.NAT_AMI_REGION_MAP, self._create_nat_ami_mapping())
        
        t.add_resource(self._create_vpc_with_gateway())
        t.add_resource(self._create_public_subnet())
        t.add_resource(self._create_nat())
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

    def _create_nat_ami_mapping(self):
        return {
            'us-east-1' : { 'AMI' : 'ami-303b1458' },
            'us-west-1' : { 'AMI' : 'ami-7da94839' },
            'us-west-2' : { 'AMI' : 'ami-69ae8259' }
            #'eu-west-1'
            #'eu-west-2'
            #'eu-central-1'
            #'sa-east-1'
            #'ap-southeast-1' : 
            #'ap-southeast-2' : 
            #'ap-northeast-1' : 
            }
        
    def _create_vpc_with_gateway(self):
        self.vpc = VPC('{0}VPC'.format(self.name),
                       CidrBlock = Ref(self.PARM_VPC_CIDR),
                       Tags = self.default_tags)
        self.igw = InternetGateway('{0}InternetGateway'.format(self.name), Tags = self.default_tags)
        self.igw_attach = VPCGatewayAttachment('{0}GatewayAttachment'.format(self.name),
                                               InternetGatewayId = Ref(self.igw),
                                               VpcId = Ref(self.vpc))
        return [self.vpc, self.igw, self.igw_attach]

    def _create_public_subnet(self):
        name_public = '{0}Public'.format(self.name)
        tags = self.default_tags + Tags(Name = name_public)
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
        nacl_assoc = SubnetNetworkAclAssociation('{0}{1}'.format(self.pub_subnet.name, self.pub_nacl.name),
                                            SubnetId = Ref(self.pub_subnet),
                                            NetworkAclId = Ref(self.pub_nacl))
        rt_assoc = SubnetRouteTableAssociation('{0}{1}'.format(self.pub_subnet.name, self.pub_rt.name),
                                               SubnetId = Ref(self.pub_subnet),
                                               RouteTableId = Ref(self.pub_rt))
        igw_route = Route('{0}Route'.format(name_public),
                          RouteTableId = Ref(self.pub_rt),
                          DependsOn = self.igw_attach.name,
                          GatewayId = Ref(self.igw),
                          DestinationCidrBlock = CIDR_ANY)
        
        nb = NaclBuilder(self.pub_nacl)
        nb.ingress().allow().http().https().ssh().ephemeral()
        nb.egress().allow().http().https().ephemeral().ssh(Ref(self.PARM_PRIV_CIDR))

        return [self.pub_subnet, self.pub_rt, self.pub_nacl, nacl_assoc, rt_assoc, igw_route] + nb.resources()

    def _create_nat(self):
        name_nat = self._fname('{0}NAT')
        tags = self.default_tags + Tags(Name = name_nat)
        sg_ingress = SecurityGroupRuleBuilder(Ref(self.PARM_PRIV_CIDR)).http().https().ssh(CIDR_ANY)
        sg_egress = SecurityGroupRuleBuilder().http().https()
        self.nat_sg = SecurityGroup('{0}NATSecurityGroup'.format(name_nat),
                                    VpcId = Ref(self.vpc),
                                    GroupDescription = 'NAT Security Group',
                                    SecurityGroupEgress = sg_egress.rules(),
                                    SecurityGroupIngress = sg_ingress.rules(),
                                    Tags = self.default_tags)
        ni = NetworkInterfaceProperty(
            AssociatePublicIpAddress = True,
            DeleteOnTermination = True,
            DeviceIndex = 0,
            GroupSet = [Ref(self.nat_sg)],
            SubnetId = Ref(self.pub_subnet)
            )
        self.nat = Instance(name_nat,
                            DependsOn = self.vpc.name,
                            KeyName = Ref(self.PARM_KEY_NAME),
                            SourceDestCheck = 'false',
                            ImageId = FindInMap(self.NAT_AMI_REGION_MAP, self.region_ref, 'AMI'),
                            InstanceType = 't2.micro',
                            NetworkInterfaces = [ni],
                            Tags = tags,
                            UserData = Base64(Join('\n', [
                                '#!/bin/bash',
                                'yum update -y && yum install -y yum-cron && chkconfig yum-cron on'
                                ])))
        return [self.nat_sg, self.nat]


    def _create_private_subnet(self):
        name_private = self._fname('{0}Private')
        tags = self.default_tags + Tags(Name = name_private)
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
                          DestinationCidrBlock = CIDR_ANY)

        nb = NaclBuilder(self.priv_nacl)
        nb.ingress().allow(pub_cidr_ref).ssh().ephemeral(CIDR_ANY)
        nb.egress().allow().http().https().ephemeral(pub_cidr_ref)

        return [self.priv_subnet, self.priv_rt, self.priv_nacl, nacl_assoc, rt_assoc, nat_route] + nb.resources()

    def _create_outputs(self):
        return [
            Output('PublicSubnet', Value = Ref(self.pub_subnet)),
            Output('PrivateSubnet', Value = Ref(self.priv_subnet)),
            Output('NATIP', Value = GetAtt(self.nat, 'PublicIp')),
            # TODO: IP of the Bastion
            ]

    def _fname(self, fmt):
        return fmt.format(self.name)

if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'Simple'
    print SimpleVPC(name).to_json()
