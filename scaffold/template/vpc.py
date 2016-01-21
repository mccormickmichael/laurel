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
        rule = ec2.NetworkAclEntry('{0}{1}'.format(self.nacl.name, name),
                                   NetworkAclId = tp.Ref(self.nacl),
                                   RuleNumber = str(number),
                                   Protocol = protocol,
                                   PortRange = ec2.PortRange(From = from_port, To = to_port),
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
        self._rules.append(ec2.SecurityGroupRule(
            CidrIp = cidr,
            FromPort = port_from,
            ToPort = port_to,
            IpProtocol = protocol))

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
    def add_resources(self, resources):
        self.add_resource(resources)

    def add_output(self, outputs):
        self.template.add_output(outputs)

    def _rename(self, fmt):
        return retag(self.default_tags, Name = fmt.format(self.name))
        
def _asref(o):
    return o if isinstance(o, tp.Ref) else tp.Ref(o)


def az_name(region, az):
    if az.startswith(region):
        return az
    return region + az.lower()
