#!/usr/bin/python

# Common functions and builders for VPC Templates

import troposphere as tp
import troposphere.ec2 as ec2


CIDR_ANY = '0.0.0.0/0'
CIDR_NONE = '0.0.0.0/32'

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
    return ec2.SecurityGroupRule(CidrIp=cidr,
                                 FromPort=from_port,
                                 ToPort=to_port,
                                 IpProtocol=protocol)


def nacl_ingress(name, nacl, number, ports, protocol, cidr=CIDR_ANY, action='allow'):
    return _nacl_rule(name, nacl, number, ports, protocol, False, cidr, action)


def nacl_egress(name, nacl, number, ports, protocol, cidr=CIDR_ANY, action='allow'):
    return _nacl_rule(name, nacl, number, ports, protocol, True, cidr, action)


def _nacl_rule(name, nacl, number, ports, protocol, egress, cidr, action):
    from_port, to_port = _asduo(ports)
    return ec2.NetworkAclEntry(name,
                               NetworkAclId=_asref(nacl),
                               RuleNumber=number,
                               Protocol=protocol,
                               PortRange=ec2.PortRange(From=from_port, To=to_port),
                               Egress=egress,
                               RuleAction=action,
                               CidrBlock=cidr)


def _asduo(d):
    return d if type(d) in [list, tuple] else (d, d)


def _asref(o):
    return o if isinstance(o, tp.Ref) else tp.Ref(o)


def az_name(region, az):
    if az.startswith(region):
        return az
    return region + az.lower()
