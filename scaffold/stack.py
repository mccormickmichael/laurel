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

class RouteBuilder:
    def __init__(self, tmpl, acl, prefix):
        self.tmpl = tmpl
        self.acl = acl
        self.prefix = prefix
        self.ingress_rule_number = 100
        self.egress_rule_number = 100

    def allow_tcp(self, name, egress, rule_number, cidr_block, port_from, port_to = None):
        port_to = port_from if not port_to else port_to
        self.tmpl.add_resource(
            NetworkAclEntry(name,
                            NetworkAclId = Ref(self.acl),
                            RuleNumber = str(rule_number),
                            Protocol = '6',
                            PortRange = PortRange(From = port_from, To = port_to),
                            Egress = str(egress).lower(),
                            RuleAction = 'allow',
                            CidrBlock = cidr_block))

    def allow_tcp_egress(self, name, cidr_block, port_from, port_to = None):
        self.allow_tcp(name, True, self.egress_rule_number, cidr_block, port_from, port_to)
        self.egress_rule_number += 1

    def allow_tcp_ingress(self, name, cidr_block, port_from, port_to = None):
        self.allow_tcp(name, False, self.ingress_rule_number, cidr_block, port_from, port_to)
        self.ingress_rule_number += 1

    def allow_http_in(self, cidr_block = '0.0.0.0/0'):
        self.allow_tcp_ingress('{0}HttpIn'.format(self.prefix), cidr_block, 80)

    def allow_https_in(self, cidr_block = '0.0.0.0/0'):
        self.allow_tcp_ingress('{0}HttpsIn'.format(self.prefix), cidr_block, 443)

    def allow_ssh_in(self, cidr_block = '0.0.0.0/0'):
        self.allow_tcp_ingress('{0}SSHIn'.format(self.prefix), cidr_block, 22)

    def allow_return_in(self, cidr_block = '0.0.0.0/0'):
        self.allow_tcp_ingress('{0}EphemeralReturnIn'.format(self.prefix), cidr_block, 49152, 65535)
        
    def allow_http_out(self, cidr_block = '0.0.0.0/0'):
        self.allow_tcp_egress('{0}HttpOut'.format(self.prefix), cidr_block, 80)

    def allow_https_out(self, cidr_block = '0.0.0.0/0'):
        self.allow_tcp_egress('{0}HttpsOut'.format(self.prefix), cidr_block, 443)

    def allow_return_out(self, cidr_block = '0.0.0.0/0'):
        self.allow_tcp_egress('{0}EphemeralReturnOut'.format(self.prefix), cidr_block, 49152, 65535)
        
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
    rb = RouteBuilder(t, pub_network_acl, 'Public')
    rb.allow_http_in()
    rb.allow_https_in()
    rb.allow_ssh_in()
    rb.allow_return_in()
    rb.allow_http_out()
    rb.allow_https_out()
    rb.allow_return_out()
    # TODO: outbound access to Private Subnets for bastions
    # TODO: Inbound access from Private Subnets to NAT


    t.add_output([
        Output('PublicSubnetA', Value = Ref(pub_subnet_a)),
        Output('PublicSubnetB', Value = Ref(pub_subnet_b))])
    
    return t.to_json()

if __name__ == "__main__":
    print create_template()

