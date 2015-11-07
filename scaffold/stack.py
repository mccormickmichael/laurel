#!/usr/bin/python
# Stand up the scaffolding stack:
# VPC (http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/getting-started-create-vpc.html)
# Public Subnet A
# Public Subnet B
# Routing Tables

# TODO:
# Private Subnet A
# Private Subnet B
# Private Subnet C (what about regions with only 2 AZs?)

from troposphere import Output, Ref, Tags, Template
from troposphere.ec2 import InternetGateway, NetworkAcl, NetworkAclEntry, PortRange, Route, RouteTable, Subnet, SubnetNetworkAclAssociation, SubnetRouteTableAssociation, VPC, VPCGatewayAttachment

az_a = 'us-west-2a' # TODO: discover?
az_b = 'us-west-2b'
az_c = 'us-west-2c'

def allow_rule(prefix, acl_id, egress, rule_number, port_from, port_to = None):
    if port_to == None:
        port_to = port_from
    return NetworkAclEntry(prefix,
                           NetworkAclId = Ref(acl_id),
                           RuleNumber = str(rule_number),
                           Protocol = '6',
                           PortRange = PortRange(From = port_from, To = port_to),
                           Egress = str(egress).lower(),
                           RuleAction = 'allow',
                           CidrBlock = '0.0.0.0/0')

def allow_ingress(prefix, acl_id, rule_number, port_from, port_to = None):
    return allow_rule('{0}In'.format(prefix), acl_id, False, rule_number, port_from, port_to)

def allow_egress(prefix, acl_id, rule_number, port_from, port_to = None):
    return allow_rule('{0}Out'.format(prefix), acl_id, True, rule_number, port_from, port_to)

def allow_http_in(prefix, acl_id, rule_number):
    return allow_ingress('{0}Http'.format(prefix), acl_id, rule_number, 80)

def allow_https_in(prefix, acl_id, rule_number):
    return allow_ingress('{0}Https'.format(prefix), acl_id, rule_number, 443)

def allow_ssh_in(prefix, acl_id, rule_number):
    return allow_ingress('{0}SSH'.format(prefix), acl_id, rule_number, 22)

def allow_return_in(prefix, acl_id, rule_number):
    return allow_ingress('{0}EphemeralReturn'.format(prefix), acl_id, rule_number, 49152, 65535)

def allow_http_out(prefix, acl_id, rule_number):
    return allow_egress('{0}Http'.format(prefix), acl_id, rule_number, 80)

def allow_https_out(prefix, acl_id, rule_number):
    return allow_egress('{0}Https'.format(prefix), acl_id, rule_number, 443)

def allow_return_out(prefix, acl_id, rule_number):
    return allow_egress('{0}EphemeralReturn'.format(prefix), acl_id, rule_number, 49152, 65535)

def create_template():

    t = Template()
    t.add_description('Scaffolding stack: supports other stacks')

    ref_stack_id = Ref('AWS::StackId')
    ref_stack_name = Ref('AWS::StackName')

    # VPC and direct resources
    vpc = t.add_resource(
        VPC('Scaffold',
            CidrBlock='172.30.0.0/16',
            Tags = Tags(Application = ref_stack_id, Name = 'ScaffoldVPC')))
    pub_subnet_a = t.add_resource(
        Subnet('PublicSubnetA',
               AvailabilityZone = az_a,
               CidrBlock = '172.30.0.0/24',
               MapPublicIpOnLaunch = True,
               VpcId = Ref(vpc),
               Tags = Tags(Application = ref_stack_id)))
    pub_subnet_b = t.add_resource(
        Subnet('PublicSubnetB',
               AvailabilityZone = az_b,
               CidrBlock = '172.30.1.0/24',
               MapPublicIpOnLaunch = True,
               VpcId = Ref(vpc),
               Tags = Tags(Application = ref_stack_id)))
    pub_route_table = t.add_resource(
        RouteTable('PublicRouteTable',
                   VpcId = Ref(vpc),
                   Tags = Tags(Application = ref_stack_id)))
    pub_network_acl = t.add_resource(
        NetworkAcl('PublicNetworkAcl',
                   VpcId = Ref(vpc),
                   Tags = Tags(Application = ref_stack_id)))

    # Internet Gateway
    igw = t.add_resource(
        InternetGateway('PublicGateway',
                        Tags = Tags(Application = ref_stack_id)))
    # Wire Internet Gateway to VPC
    t.add_resource(
        VPCGatewayAttachment('PublicGatewayAttachment',
                             InternetGatewayId = Ref(igw),
                             VpcId = Ref(vpc)))

    # Wire Public Network Acl to Public Subnets
    t.add_resource(
        SubnetNetworkAclAssociation('PublicSubnetANacl',
                                    SubnetId = Ref(pub_subnet_a),
                                    NetworkAclId = Ref(pub_network_acl)))
    t.add_resource(
        SubnetNetworkAclAssociation('PublicSubnetBNacl',
                                    SubnetId = Ref(pub_subnet_b),
                                    NetworkAclId = Ref(pub_network_acl)))

    # Wire Public Route Table to Public Subnets
    t.add_resource(
        SubnetRouteTableAssociation('PublicSubnetART',
                                    SubnetId = Ref(pub_subnet_a),
                                    RouteTableId = Ref(pub_route_table)))
    t.add_resource(
        SubnetRouteTableAssociation('PublicSubnetBRT',
                                    SubnetId = Ref(pub_subnet_b),
                                    RouteTableId = Ref(pub_route_table)))

    # Wire Internet Gateway Route to Public Route Table
    pub_route = t.add_resource(
        Route('PublicRoute',
              RouteTableId = Ref(pub_route_table),
              DependsOn = 'PublicGatewayAttachment',
              GatewayId = Ref(igw),
              DestinationCidrBlock='0.0.0.0/0'))

    # Wire Network ACL rules to Public ACL
    t.add_resource(allow_http_out('Public', pub_network_acl, 100))
    t.add_resource(allow_https_out('Public', pub_network_acl, 101))
    t.add_resource(allow_return_out('Public', pub_network_acl, 200))
    # TODO: outbound access to Private Subnets for bastions
    t.add_resource(allow_http_in('Public', pub_network_acl, 100))
    t.add_resource(allow_https_in('Public', pub_network_acl, 101))
    t.add_resource(allow_ssh_in('Public', pub_network_acl, 102))
    t.add_resource(allow_return_in('Public', pub_network_acl, 200))
    # TODO: Inbound access from Private Subnets to NAT

    t.add_output([
        Output('PublicSubnetA', Value = Ref(pub_subnet_a)),
        Output('PublicSubnetB', Value = Ref(pub_subnet_b))])
    
    return t.to_json()

if __name__ == "__main__":
    print create_template()

