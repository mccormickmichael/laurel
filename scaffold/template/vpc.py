#!/usr/bin/python

# Common functions and builders for VPC Templates

import re
from troposphere import Base64, Join, Ref
from troposphere.ec2 import (Instance, InternetGateway, NetworkAcl, NetworkAclEntry, NetworkInterfaceProperty, PortRange, SecurityGroupRule, VPC, VPCGatewayAttachment)

CIDR_ANY = '0.0.0.0/0'
CIDR_NONE = '0.0.0.0/32'

cidr_re = re.compile(r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$")

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
        return self.tcp('EphemeralReturn', 32767, 65535, cidr)

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

def _asref(o):
    return o if isinstance(o, Ref) else Ref(o)

def create_vpc_with_inet_gateway(name, vpc_cidr, tags = []):
    cidr = Ref(vpc_cidr) if cidr_re.match(vpc_cidr) is None else vpc_cidr
    vpc = VPC('{}VPC'.format(name),
              CidrBlock = cidr,
              Tags = tags)
    igw = InternetGateway('{}InternetGateway'.format(name),
                          Tags = tags)
    attach = VPCGatewayAttachment('{}GatewayAttachment'.format(name),
                                  InternetGatewayId = Ref(igw),
                                  VpcId = Ref(vpc))
    return {
        'VPC': vpc,
        'InternetGateway': igw,
        'GatewayAttachment' : attach
    }

def create_nat_instance(name, sg, subnet, key_name, image_id, tags = []):
    ni = NetworkInterfaceProperty(
        AssociatePublicIpAddress = True,
        DeleteOnTermination = True,
        DeviceIndex = 0,
        GroupSet = [_asref(sg)],
        SubnetId = _asref(subnet)
    )
    # TODO: DependsOn?
    nat = Instance('{}NAT'.format(name),
                   KeyName = _asref(key_name),
                   SourceDestCheck = 'false',
                   ImageId = image_id,
                   InstanceType = 't2.micro',
                   NetworkInterfaces = [ni],
                   Tags = tags,
                   UserData = Base64(Join('\n', [
                       '#!/bin/bash',
                       'yum update -y && yum install -y yum-cron && chkconfig yum-cron on'
                   ])))
    return {
        'Instance': nat
    }
    
