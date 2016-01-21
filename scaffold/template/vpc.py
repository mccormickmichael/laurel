#!/usr/bin/python

# Common functions and builders for VPC Templates

import re
from troposphere import Base64, GetAZs, Join, Ref, Select, Tags, Template
from troposphere.ec2 import (Instance, InternetGateway, NetworkAcl, NetworkAclEntry, NetworkInterfaceProperty, PortRange, Route, RouteTable, SecurityGroupRule, Subnet, SubnetNetworkAclAssociation, SubnetRouteTableAssociation, VPC, VPCGatewayAttachment)
from . import cidr

CIDR_ANY = '0.0.0.0/0'
CIDR_NONE = '0.0.0.0/32'

REF_STACK_NAME = Ref('AWS::StackName')
REF_REGION = Ref('AWS::Region')

AMI_REGION_MAP_NAME = 'AMIRegionMap'
AMI_REGION_MAP = {
    'us-east-1' : { 'NAT' : 'ami-303b1458', 'BASTION': 'ami-60b6c60a' },
    'us-west-1' : { 'NAT' : 'ami-7da94839', 'BASTION': 'ami-d5ea86b5' },
    'us-west-2' : { 'NAT' : 'ami-69ae8259', 'BASTION': 'ami-f0091d91' }
    #'eu-west-1'
    #'eu-central-1'
    #'sa-east-1'
    #'ap-southeast-1'
    #'ap-southeast-2' 
    #'ap-northeast-1'
    #'ap-northeast-2'
}

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

    def nat_ephemeral(self, cidr = None):
        return self.tcp('EphemeralReturn', 1024, 65535, cidr)
    
    def ephemeral(self, cidr = None):
        return self.tcp('EphemeralReturn', 32767, 65535, cidr)

    def any(self, cidr = None):
        cidr = cidr or self.cidr
        self.parent._addrule('Any', self.action(), '-1', 0, 65535, cidr)
        return self

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
        self.parent._addrule(self._rulename(name), self._nextrulenum(), protocol,
                             port_from, port_to, self._egress(), action, cidr)

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
    def __init__(self, cidr = CIDR_NONE):
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

class TemplateBuilderBase(object):
    def __init__(self, name, description):
        self.name = name
        self.default_tags = Tags(Application = REF_STACK_NAME, Name = self.name)
        self.template = Template()
        self.template.add_version()
        self.template.add_description(description)
        self.template.add_mapping(AMI_REGION_MAP_NAME, AMI_REGION_MAP) 

    def to_json(self):
        return self.template.to_json()

    def add_mapping(self, mapping_name, mapping):
        self.template.add_mapping(mapping_name, mapping)

    def add_parameter(self, parameters):
        self.template.add_parameter(parameters)
    
    def add_resource(self, resource):
        self.template.add_resource(resource)
    def add_resources(self, resources):
        self.add_resource(resources)

    def add_output(self, outputs):
        self.template.add_output(outputs)
        
def _asref(o):
    return o if isinstance(o, Ref) else Ref(o)


def az_name(region, az):
    if az.startswith(region):
        return az
    return region + az.lower()

def merge_tags(src, dest):
    """Merge Troposphere Tag objects. Dest values override src values."""
    d = {}
    for st in src.tags + dest.tags:
        d[st['Key']] = st['Value']
    return Tags(**d)


# def create_nat_instance(name, sg, subnet, key_name, image_id, tags = [], dependencies = []):
#     return _create_util_instance('{}NAT'.format(name), sg, subnet, key_name, image_id, tags, dependencies)

# def create_bastion_instance(name, sg, subnet, key_name, image_id, tags = [], dependencies = []):
#     return _create_util_instance('{}Bastion'.format(name), sg, subnet, key_name, image_id, tags, dependencies)

# def _create_util_instance(name, sg, subnet, key_name, image_id, tags, dependencies):
#     dependency_names = [d.name for d in dependencies]
#     ni = NetworkInterfaceProperty(
#         AssociatePublicIpAddress = True,
#         DeleteOnTermination = True,
#         DeviceIndex = 0,
#         GroupSet = [_asref(sg)],
#         SubnetId = _asref(subnet)
#     )
#     instance = Instance(name,
#                         DependsOn = dependency_names,
#                         KeyName = _asref(key_name),
#                         SourceDestCheck = 'false',
#                         ImageId = image_id,
#                         InstanceType = 't2.micro',
#                         NetworkInterfaces = [ni],
#                         Tags = tags,
#                         UserData = Base64(Join('\n', [
#                             '#!/bin/bash',
#                             'yum update -y && yum install -y yum-cron && chkconfig yum-cron on'
#                         ])))
#     return {
#         'Instance': instance
#     }
