#!/usr/bin/python

# Creates a CloudFormation template for a VPC with N public and N private subnets.
# Each public subnet hosts a NAT server that the corresponding private subnet points to.
#
# Stack parameters (provided at stack create/update time)
# - ???
#
# Stack Outputs:
# - PublicSubnet-(N) - ID of the public subnet in availability zone (N)
# - PrivateSubnet-(N) - ID of the private subnet in availability zone (N)
#
# Template Parameters (provided at template creation time):
# - vpc_cidr
#   The CIDR block for the entire VPC. Defaults to 172.16.0.0/16
# - pub_size
#   The # of IP addresses to make available to each public subnet. Defaults to 1024
# - priv_size
#   The # of IP addresses to make available to each private subnet. Defaults to 2048
# - region
#   The region for which to build the template
# - availability_zones
#   A sequence of availability zone suffixes in which to place the subnets. The length
#   of the sequence will determine the numeber of public/private subnets. Alternatively,
#   specify the full name of each availability zone.
#   Examples: ('a', 'b', 'e'), ('us-west-2a', 'us-west-2b', 'us-west-2c')

import sys
import troposphere as tp
from . import cidr, vpc

class NxNVPC(vpc.TemplateBuilderBase):

    def __init__(self, name, description = '[REPLACEME]',
                 vpc_cidr = '172.16.0.0/16',
                 region = 'us-west-2',
                 availability_zones = ('a', 'b', 'c'),
                 pub_size = 1024,
                 priv_size = 2048):
        super(NxNVPC, self).__init__(name, description)

        self.vpc_cidr = vpc_cidr
        self.vpc_cidr_alloc = cidr.CidrBlockAllocator(vpc_cidr)
        self.region = region
        self.azs = availability_zones
        self.pub_size = pub_size
        self.priv_size = priv_size

        self.default_tags = tp.Tags()

        self.create_vpc()
        self.create_public_routes()
        self.create_public_nacl()

        self.pub_subnets = {}
        self.priv_subnets = {}
        self.create_private_nacl()
        for az in self.azs:
            self.create_subnets_in_az(az)

        # self.create_outputs()

    def create_vpc(self):
        self.vpc = tp.ec2.VPC('{}VPC'.format(self.name),
                              CidrBlock = self.vpc_cidr,
                              Tags = self.default_tags)
        self.igw = tp.ec2.InternetGateway('{}InternetGateway'.format(self.name),
                                          Tags = self.default_tags)
        self.igw_attach = tp.ec2.VPCGatewayAttachment('{}GatewayAttachment'.format(self.name),
                                                      InternetGatewayId = tp.Ref(self.igw),
                                                      VpcId = tp.Ref(self.vpc))
        self.add_resources([self.vpc, self.igw, self.igw_attach])

    def create_public_routes(self):
        self.public_route_table = tp.ec2.RouteTable('{}PublicRT'.format(self.name),
                                                    VpcId = tp.Ref(self.vpc),
                                                    Tags = self.default_tags)
        route = tp.ec2.Route('{}PublicRoute'.format(self.name),
                             RouteTableId = tp.Ref(self.public_route_table),
                             DependsOn = self.igw.name,
                             GatewayId = tp.Ref(self.igw),
                             DestinationCidrBlock = vpc.CIDR_ANY)
        
        self.add_resources([self.public_route_table, route])

    def create_public_nacl(self):
        self.public_nacl = tp.ec2.NetworkAcl('{}PublicNacl'.format(self.name),
                                             VpcId = tp.Ref(self.vpc),
                                             Tags = self.default_tags)
        self.add_resource(self.public_nacl)
        self.create_public_nacl_rules(self.public_nacl)

    def create_public_nacl_rules(self, pub_nacl):
        builder = vpc.NaclBuilder(pub_nacl)
        builder.ingress().allow().http().https().ssh().ephemeral()
        builder.egress().allow().any()
        self.add_resources(builder.resources())

    def create_subnets_in_az(self, az):
        az = vpc.az_name(self.region, az)
        pub_subnet = self.create_public_subnet(az)

        priv_rt = self.create_private_route_table(az)
        priv_subnet = self.create_private_subnet(az, priv_rt)
        nat_sg = self.create_nat_sg(pub_subnet)
        nat_eni = self.create_nat_eni(pub_subnet, nat_sg)
        self.route_private_subnet(priv_subnet, priv_rt, nat_eni)
        
        # Private Route -> ENI
        # NAT (optional)

    def _create_subnet(self, prefix, az, size, nacl, rt):
        subnet = tp.ec2.Subnet('{}{}Subnet{}'.format(self.name, prefix, az[-1].upper()),
                               AvailabilityZone = az,
                               CidrBlock = str(self.vpc_cidr_alloc.alloc(size)),
                               MapPublicIpOnLaunch = False,
                               VpcId = tp.Ref(self.vpc),
                               Tags = self.default_tags)
        self.add_resource(subnet)
        self.add_resource(tp.ec2.SubnetRouteTableAssociation('{}{}RTAssoc'.format(subnet.name, prefix),
                                                             SubnetId = tp.Ref(subnet),
                                                             RouteTableId = tp.Ref(rt)))
        self.add_resource(tp.ec2.SubnetNetworkAclAssociation('{}{}NaclAssoc'.format(subnet.name, prefix),
                                                             SubnetId = tp.Ref(subnet),
                                                             NetworkAclId = tp.Ref(nacl)))
        self.add_output(tp.Output(subnet.name, Value = tp.Ref(subnet)))
        return subnet

        
    def create_public_subnet(self, az):
        pub_subnet = self._create_subnet('Public', az, self.pub_size, self.public_nacl, self.public_route_table)
        self.pub_subnets[pub_subnet.name] = pub_subnet
        return pub_subnet

    def create_private_subnet(self, az, rt):
        priv_subnet = self._create_subnet('Private', az, self.priv_size, self.priv_nacl, rt)
        self.pub_subnets[priv_subnet.name] = priv_subnet
        return priv_subnet

    def create_private_route_table(self, az):
        rt = tp.ec2.RouteTable('{}PrivateRT{}'.format(self.name, az[-1].upper()),
                               VpcId = tp.Ref(self.vpc),
                               Tags = self.default_tags)
        self.add_resource(rt)
        return rt

    def create_private_nacl(self):
        self.priv_nacl = tp.ec2.NetworkAcl('{}PrivateNacl'.format(self.name),
                                      VpcId = tp.Ref(self.vpc),
                                      Tags = self.default_tags)
        self.add_resource(self.priv_nacl)
        self.create_private_nacl_rules(self.priv_nacl)

    def create_private_nacl_rules(self, nacl):
        builder = vpc.NaclBuilder(nacl)
        builder.ingress().allow(self.vpc_cidr).http().https().ssh().ephemeral()
        builder.egress().allow().any()
        self.add_resources(builder.resources())

    def create_nat_sg(self, subnet):
        # TODO: This SG could be shared across pub subnets if the ingress cidr block is the VPC.
        #       Is there a reason that could be bad?
        sg = tp.ec2.SecurityGroup('{}NatSg'.format(subnet.name),
                                  GroupDescription = 'NAT Instance Security Group for {}'.format(subnet.name),
                                  SecurityGroupIngress = vpc.SecurityGroupRuleBuilder(subnet.CidrBlock).any().rules(),
                                  VpcId = tp.Ref(self.vpc),
                                  Tags = self.default_tags)
        self.add_resource(sg)
        return sg

    def create_nat_eni(self, subnet, sg):
        eni = tp.ec2.NetworkInterface('{}NatEni'.format(subnet.name),
                                      GroupSet = [tp.Ref(sg)],
                                      SubnetId = tp.Ref(subnet),
                                      SourceDestCheck = False,
                                      Tags = self.default_tags)
        self.add_resource(eni)
        self.add_output(tp.Output(eni.name, Value = tp.Ref(eni)))
        return eni

    def route_private_subnet(self, subnet, rt, eni):
        route = tp.ec2.Route('{}PrivateRoute'.format(subnet.name),
                             RouteTableId = tp.Ref(rt),
                             NetworkInterfaceId = tp.Ref(eni),
                             DestinationCidrBlock = vpc.CIDR_ANY)
        self.add_resource(route)
    
if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'Simple'
    print NxNVPC(name).to_json()
