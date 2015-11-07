#!/usr/bin/python
# Stand up the scaffolding stack:
# VPC (http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/getting-started-create-vpc.html)


# Public Subnet A
# Public Subnet B
# Private Subnet A
# Private Subnet B
# Private Subnet C (what about regions with only 2 AZs?)
# Routing Tables


from troposphere import Output, Ref, Tags, Template
from troposphere.ec2 import InternetGateway, NetworkAcl, NetworkAclEntry, PortRange, Route, RouteTable, Subnet, SubnetNetworkAclAssociation, SubnetRouteTableAssociation, VPC, VPCGatewayAttachment

az_a = 'us-west-2a' # TODO: discover?
az_b = 'us-west-2b'
az_c = 'us-west-2c'

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
    t.add_resource(
        NetworkAclEntry('PublicHttpOut',
                        NetworkAclId = Ref(pub_network_acl),
                        RuleNumber = '100',
                        Protocol = '6',
                        PortRange = PortRange(From = 80, To = 80),
                        Egress='true',
                        RuleAction = 'allow',
                        CidrBlock = '0.0.0.0/0'))
    t.add_resource(
        NetworkAclEntry('PublicHttpsOut',
                        NetworkAclId = Ref(pub_network_acl),
                        RuleNumber = '101',
                        Protocol = '6',
                        PortRange = PortRange(From = 443, To = 443),
                        Egress='true',
                        RuleAction = 'allow',
                        CidrBlock = '0.0.0.0/0'))
    t.add_resource(
        NetworkAclEntry('PublicEphemeralOutReturn',
                        NetworkAclId = Ref(pub_network_acl),
                        RuleNumber = '200',
                        Protocol = '6',
                        PortRange = PortRange(From = 49152, To = 65535),
                        Egress='true',
                        RuleAction = 'allow',
                        CidrBlock = '0.0.0.0/0'))
    # TODO: outbound access to Private Subnets for bastions
    t.add_resource(
        NetworkAclEntry('PublicHttpIn',
                        NetworkAclId = Ref(pub_network_acl),
                        RuleNumber = '100',
                        Protocol = '6',
                        PortRange = PortRange(From = 80, To = 80),
                        Egress='false',
                        RuleAction = 'allow',
                        CidrBlock = '0.0.0.0/0'))
    t.add_resource(
        NetworkAclEntry('PublicHttpsIn',
                        NetworkAclId = Ref(pub_network_acl),
                        RuleNumber = '101',
                        Protocol = '6',
                        PortRange = PortRange(From = 443, To = 443),
                        Egress='false',
                        RuleAction = 'allow',
                        CidrBlock = '0.0.0.0/0'))
    t.add_resource(
        NetworkAclEntry('PublicSSHIn',
                        NetworkAclId = Ref(pub_network_acl),
                        RuleNumber = '102',
                        Protocol = '6',
                        PortRange = PortRange(From = 22, To = 22),
                        Egress='false',
                        RuleAction = 'allow',
                        CidrBlock = '0.0.0.0/0'))
    t.add_resource(
        NetworkAclEntry('PublicEphemeralInReturn',
                        NetworkAclId = Ref(pub_network_acl),
                        RuleNumber = '200',
                        Protocol = '6',
                        PortRange = PortRange(From = 49152, To = 65535),
                        Egress='false',
                        RuleAction = 'allow',
                        CidrBlock = '0.0.0.0/0'))
    # TODO: Inbound access from Private Subnets to NAT

    t.add_output([
        Output('PublicSubnetA', Value = Ref(pub_subnet_a)),
        Output('PublicSubnetB', Value = Ref(pub_subnet_b))])
    
    return t.to_json()

if __name__ == "__main__":
    print create_template()
