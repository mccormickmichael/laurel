#!/usr/bin/python

# Common functions and builders for VPC Templates

import re
import troposphere as tp
import troposphere.ec2 as ec2
from . import cidr
from . import retag

CIDR_ANY = '0.0.0.0/0'
CIDR_NONE = '0.0.0.0/32'

REF_STACK_NAME = tp.Ref('AWS::StackName')
REF_REGION = tp.Ref('AWS::Region')

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

HTTP = 80
HTTPS = 443
SSH = 22
EPHEMERAL = (32767, 65536)
NAT = (1024, 65535)
ANY_PORT = (0, 65535)

TCP = '6'
UDP = '17'
ICMP = '1'
ANY_PROTOCOL = '-1'

def sg_rule(cidr, ports, protocol):
    from_port, to_port = _asduo(ports)
    return ec2.SecurityGroupRule(CidrIp = cidr,
                                 FromPort = from_port,
                                 ToPort = to_port,
                                 IpProtocol = protocol)

def nacl_ingress(name, nacl, number, ports, protocol, cidr = CIDR_ANY, action = 'allow'):
    return _nacl_rule(name, nacl, number, ports, protocol, False, cidr, action)

def nacl_egress(name, nacl, number, ports, protocol, cidr = CIDR_ANY, action = 'allow'):
    return _nacl_rule(name, nacl, number, ports, protocol, True, cidr, action)

def _nacl_rule(name, nacl, number, ports, protocol, egress, cidr, action):
    from_port, to_port = _asduo(ports)
    return ec2.NetworkAclEntry(name,
                               NetworkAclId = _asref(nacl),
                               RuleNumber = number,
                               Protocol = protocol,
                               PortRange = ec2.PortRange(From = from_port, To = to_port),
                               Egress = egress,
                               RuleAction = action,
                               CidrBlock = cidr)
                               
class TemplateBuilderBase(object):
    def __init__(self, name, description):
        self.name = name
        self.default_tags = tp.Tags(Application = REF_STACK_NAME, Name = self.name)
        self.template = tp.Template()
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
        
    def add_resources(self, *resources):
        self.add_resource(list(resources))

    def add_output(self, outputs):
        self.template.add_output(outputs)

    def _rename(self, fmt):
        return retag(self.default_tags, Name = fmt.format(self.name))
        
def _asduo(d):
    return d if type(d) in [list, tuple] else (d, d)

def _asref(o):
    return o if isinstance(o, tp.Ref) else tp.Ref(o)


def az_name(region, az):
    if az.startswith(region):
        return az
    return region + az.lower()
