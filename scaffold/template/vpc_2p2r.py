#!/usr/bin/python

# VPC with 2 Public subnets and 2 private subnets
# (http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/getting-started-create-vpc.html)
#
# Parameters:
# BastionKey: the public key name for the Bastion server
# VpcCidr: the CIDR block of the VPC. Defaults to 172.16.0.0/16
#
# Stack Outputs:
# BastionIP:     The public IP of the bastion server
# PublicSubnet0: The ID of public subnet 0
# PublicSubnet1: The ID of public subnet 1
# PrivateSubnet0: The ID of private subnet 0
# PrivateSubnet1: The ID of private subnet 1

from troposphere import Output, Ref, Tags, Template
from troposphere.ec2 import InternetGateway, NetworkAcl, NetworkAclEntry, PortRange, Route, RouteTable, Subnet, SubnetNetworkAclAssociation, SubnetRouteTableAssociation, VPC, VPCGatewayAttachment

class TwoPublicPrivate(object):

    PARM_KEY_NAME = 'KeyNameParameter'
    PARM_VPC_CIDR = 'VpcCidrParameter'

    DEFAULT_PARM_VPC_CIDR = '172.16.0.0/16'

    stack_name_ref = Ref('AWS::StackName')
    region_ref = Ref('AWS::Region')

    def __init__(self, name,
                 description = 'VPC with 2 public subnets and 2 private subnets',
                 pub_subnet_size = 256,
                 priv_subnet_size = 1024):
        self.name = name
        self.default_tage = Tags(Application = stack_name_ref, Name = self.name)

        t = Template()
        t.add_version()

        t.add_description(description)

        self.t = t

    def to_json():
        return self.t.to_json()


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'Sample'
    print TwoPublicPrivate(name).to_json()
    
# class RouteBuilder:
#     def __init__(self, tmpl, acl, prefix, action, egress, cidr_block = '0.0.0.0/0'):
#         if action not in ['allow', 'deny']:
#             raise ValueError("'action' must be one of ['allow', 'deny']")
#         self.tmpl = tmpl
#         self.acl = acl
#         self.prefix = prefix
#         self.action = action
#         self.egress = egress
#         self.cidr_block = cidr_block
#         self.rule_number = 100

#     def __add_tcp(self, protocol, port_from, port_to = None):
#         port_to = port_from if not port_to else port_to
#         self.tmpl.add_resource(
#             NetworkAclEntry('{0}{1}{2}'.format(self.prefix, protocol, 'Out' if self.egress else 'In'),
#                             NetworkAclId = Ref(self.acl),
#                             RuleNumber = str(self.rule_number),
#                             Protocol = '6',
#                             PortRange = PortRange(From = port_from, To = port_to),
#                             Egress = str(self.egress).lower(),
#                             RuleAction = self.action,
#                             CidrBlock = self.cidr_block))
#         self.rule_number += 1
#         return self

#     def http(self):
#         return self.__add_tcp('Http', 80)

#     def https(self):
#         return self.__add_tcp('Https', 443)

#     def ssh(self):
#         return self.__add_tcp('SSH', 22)

#     def response(self):
#         return self.__add_tcp('EphemeralReturn', 49152, 65535)
        
# def create_template():

#     t = Template()
#     t.add_description('Scaffolding stack: supports other stacks')

#     ref_stack_id = Ref('AWS::StackId')
#     ref_stack_name = Ref('AWS::StackName')

#     # VPC and direct resources
#     vpc = t.add_resource(
#         VPC('Scaffold',
#             CidrBlock='172.30.0.0/16',
#             Tags = Tags(Application = ref_stack_id, Name = 'ScaffoldVPC')))
#     pub_subnet_a = t.add_resource(
#         Subnet('PublicSubnetA',
#                AvailabilityZone = az_a,
#                CidrBlock = '172.30.0.0/24',
#                MapPublicIpOnLaunch = True,
#                VpcId = Ref(vpc),
#                Tags = Tags(Application = ref_stack_id)))
#     pub_subnet_b = t.add_resource(
#         Subnet('PublicSubnetB',
#                AvailabilityZone = az_b,
#                CidrBlock = '172.30.1.0/24',
#                MapPublicIpOnLaunch = True,
#                VpcId = Ref(vpc),
#                Tags = Tags(Application = ref_stack_id)))
#     pub_route_table = t.add_resource(
#         RouteTable('PublicRouteTable',
#                    VpcId = Ref(vpc),
#                    Tags = Tags(Application = ref_stack_id)))
#     pub_network_acl = t.add_resource(
#         NetworkAcl('PublicNetworkAcl',
#                    VpcId = Ref(vpc),
#                    Tags = Tags(Application = ref_stack_id)))

#     # Internet Gateway
#     igw = t.add_resource(
#         InternetGateway('PublicGateway',
#                         Tags = Tags(Application = ref_stack_id)))
#     # Wire Internet Gateway to VPC
#     t.add_resource(
#         VPCGatewayAttachment('PublicGatewayAttachment',
#                              InternetGatewayId = Ref(igw),
#                              VpcId = Ref(vpc)))

#     # Wire Public Network Acl to Public Subnets
#     t.add_resource(
#         SubnetNetworkAclAssociation('PublicSubnetANacl',
#                                     SubnetId = Ref(pub_subnet_a),
#                                     NetworkAclId = Ref(pub_network_acl)))
#     t.add_resource(
#         SubnetNetworkAclAssociation('PublicSubnetBNacl',
#                                     SubnetId = Ref(pub_subnet_b),
#                                     NetworkAclId = Ref(pub_network_acl)))

#     # Wire Public Route Table to Public Subnets
#     t.add_resource(
#         SubnetRouteTableAssociation('PublicSubnetART',
#                                     SubnetId = Ref(pub_subnet_a),
#                                     RouteTableId = Ref(pub_route_table)))
#     t.add_resource(
#         SubnetRouteTableAssociation('PublicSubnetBRT',
#                                     SubnetId = Ref(pub_subnet_b),
#                                     RouteTableId = Ref(pub_route_table)))

#     # Wire Internet Gateway Route to Public Route Table
#     pub_route = t.add_resource(
#         Route('PublicRoute',
    #           RouteTableId = Ref(pub_route_table),
    #           DependsOn = 'PublicGatewayAttachment',
    #           GatewayId = Ref(igw),
    #           DestinationCidrBlock='0.0.0.0/0'))

    # # Wire Network ACL rules to Public ACL
    # rb_in = RouteBuilder(t, pub_network_acl, 'Public', 'allow', False)
    # rb_in.http().https().ssh().response()

    # rb_out = RouteBuilder(t, pub_network_acl, 'Public', 'allow', True)
    # rb_out.http().https().response()
    # # TODO: outbound access to Private Subnets for bastions
    # # TODO: Inbound access from Private Subnets to NAT


    # t.add_output([
    #     Output('PublicSubnetA', Value = Ref(pub_subnet_a)),
    #     Output('PublicSubnetB', Value = Ref(pub_subnet_b))])
    
    # return t.to_json()


