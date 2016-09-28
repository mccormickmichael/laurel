# Define a CloudFormation template to host a tiny ELK stack. This stack hosts Logstash and Elasticsearch
# on the same server in a private subnet, and hosts Kibana in a separate server in a public subnet.
# The Logstash instance listens for logs shipped from Beats
#
# Template Parameters (provided at templat creation time):
# - name
#   Name of the stack, of course. Required.
# - description
#   Description of the stack. Please provide one.
# - region
#   The AWS region in which this template will be executed
# - bucket
#   The S3 bucket where configuration and deployment files are located
# - vpc_id
#   ID of the VPC in which this stack is built
# - vpc_cidr
#   CIDR block of the vpc
# - es_subnet_id
#   List of the subnet in which the Logstash/Elasticsearch server should be built.
# - kibana_subnet_ids
#   List of subnets in which the kibana server should be built.
# - es_instance_type
#   Instance type of the server instances. Defaults to t2.micro
# - kibana_instance_type
#   Instance type of the ui instances. Defaults to t2.micro
#
# Stack Parameters (provided to the template at stack create/update time):
#
# - ServerKey
#   Name of the key pair to use to connect to server instances
#
# Stack Outputs:
#
# - ElasticSearchASG
#   ID of the autoscaling group controlling the Nth cluster member
# - ElasticSearchENI
#   ID of the elastic network interface attached to the Logstash/ElasticSearch server

from scaffold.cf.template import TemplateBuilder, asgtag
from scaffold.cf import net
from scaffold.iam import service_role_policy_doc

import troposphere as tp
import troposphere.autoscaling as asg
import troposphere.cloudformation as cf
import troposphere.ec2 as ec2
import troposphere.iam as iam

from . import UserDataSegments
from . import configsets


AMI_REGION_MAP_NAME = 'AMIRegionMap'
AMI_REGION_MAP = {
    'us-east-1': {'ES': 'ami-3bdd502c', 'KIBANA': 'ami-3bdd502c'},
    'us-west-1': {'ES': 'ami-48db9d28', 'KIBANA': 'ami-48db9d28'},
    'us-west-2': {'ES': 'ami-d732f0b7', 'KIBANA': 'ami-d732f0b7'}
    # 'eu-west-1'
    # 'eu-central-1'
    # 'sa-east-1'
    # 'ap-southeast-1'
    # 'ap-southeast-2'
    # 'ap-northeast-1'
    # 'ap-northeast-2'
}


class TinyElkTemplate(TemplateBuilder):

    BUILD_PARM_NAMES = ['vpc_id', 'vpc_cidr', 'es_subnet_id', 'kibana_subnet_ids', 'es_instance_type', 'kibana_instance_type']

    SERVER_KEY_PARM_NAME = 'ServerKey'

    def __init__(self, name,
                 region,
                 bucket,
                 bucket_key_prefix,
                 vpc_id,
                 vpc_cidr,
                 es_subnet_id,
                 kibana_subnet_ids,
                 description='[REPLACEME]',
                 es_instance_type='t2.micro',
                 kibana_instance_type='t2.micro'):
        super(TinyElkTemplate, self).__init__(name, description, TinyElkTemplate.BUILD_PARM_NAMES)

        self.region = region
        self.bucket = bucket
        self.bucket_key_prefix = bucket_key_prefix
        self.vpc_id = vpc_id
        self.vpc_cidr = vpc_cidr
        self.es_subnet_id = es_subnet_id
        self.kibana_subnet_ids = kibana_subnet_ids
        self.es_instance_type = es_instance_type
        self.kibana_instance_type = kibana_instance_type

    def internal_add_mappings(self):
        self.template.add_mapping(AMI_REGION_MAP_NAME, AMI_REGION_MAP)

    def internal_build_template(self):
        self.create_parameters()

        self.create_elasticsearch()
        self.create_kibana()

    def create_parameters(self):
        self.add_parameter(tp.Parameter(self.SERVER_KEY_PARM_NAME, Type='String'))

    def create_elasticsearch(self):
        sg = self._create_es_sg()
        iam_profile = self._create_es_iam_profile()
        eni = self._create_es_eni(sg)
        self._create_es_asg(sg, iam_profile, eni)

    def _create_es_sg(self):
        ingress_rules = [
            net.sg_rule(self.vpc_cidr, (9200, 9400), net.TCP),  # Elasticsearch
            net.sg_rule(self.vpc_cidr, 5044, net.TCP),  # Beats
            net.sg_rule(self.vpc_cidr, 22, net.TCP)     # SSH. Remove if you don't need it.
        ]
        elasticsearch_sg = ec2.SecurityGroup('ElasticsearchSecurityGroup',
                                             GroupDescription='SecurityGroup for ElasticSearch and Logstash',
                                             SecurityGroupIngress=ingress_rules,
                                             VpcId=self.vpc_id,
                                             Tags=self.default_tags)
        self.add_resource(elasticsearch_sg)
        self.output_ref('ElasticsearchSG', elasticsearch_sg)
        return elasticsearch_sg

    def _create_es_iam_profile(self):
        policy = iam.Policy(
            PolicyName='ElasticsearchInstance',
            PolicyDocument={
                'Statement': [{
                    'Effect': 'Allow',
                    'Resource': ['*'],
                    'Action': ['ec2:Attach*', 'ec2:Describe*']
                }, {
                    'Effect': 'Allow',
                    'Resource': 'arn:aws:s3:::{}/*'.format(self.bucket),
                    'Action': ['s3:Get*']
                }]
            })
        role = iam.Role('ElasticsearchInstanceRole',
                        AssumeRolePolicyDocument=service_role_policy_doc.ec2,
                        Policies=[policy])
        profile = iam.InstanceProfile('ElasticsearchInstanceProfile',
                                      Path='/',
                                      Roles=[tp.Ref(role)])
        self.add_resources(role, profile)
        return profile

    def _create_es_eni(self, sg):
        eni = ec2.NetworkInterface('ElasticsearchENI',
                                   Description='ENI for the Elasticsearch server node',
                                   GroupSet=[tp.Ref(sg)],
                                   SourceDestCheck=True,
                                   SubnetId=self.es_subnet_id,
                                   Tags=self._rename('{} ES ENI'))
        self.es_eni = eni
        self.add_resource(eni)
        self.output(eni)
        return eni

    def _create_es_asg(self, sg, iam_profile, eni):
        asg_name = 'ElasticsearchASG'

        user_data = self._create_es_userdata(asg_name, eni)
        lc = asg.LaunchConfiguration('ElasticsearchLC',
                                     ImageId=tp.FindInMap(AMI_REGION_MAP_NAME, self.region, 'ES'),
                                     InstanceType=self.es_instance_type,
                                     SecurityGroups=[tp.Ref(sg)],
                                     KeyName=tp.Ref(self.SERVER_KEY_PARM_NAME),
                                     IamInstanceProfile=tp.Ref(iam_profile),
                                     InstanceMonitoring=False,
                                     AssociatePublicIpAddress=False,
                                     UserData=user_data)
        group = asg.AutoScalingGroup(asg_name,
                                     MinSize=1,
                                     MaxSize=1,
                                     LaunchConfigurationName=tp.Ref(lc),
                                     VPCZoneIdentifier=[self.es_subnet_id],
                                     Tags=asgtag(self._rename('{} Elasticsearch')))
        group.Metadata = self._create_es_metadata()
        self.add_resources(lc, group)

        self.output(group)

    def _create_es_userdata(self, asg_name, eni):
        startup = self._common_userdata() \
                  + UserDataSegments.attach_eni(eni) \
                  + UserDataSegments.eni_to_ip(eni, '/tmp/es_network_host') \
                  + UserDataSegments.invoke_cfn_init(asg_name, self._es_configset_names())
        return tp.Base64(tp.Join('', startup))

    def _create_es_metadata(self):
        return cf.Metadata(
            self._create_es_cf_init()
        )

    # TODO: it seems we could do a better job tying these into the configset names.
    def _create_es_cf_init(self):
        network_config = configsets.NetworkInterfaceAttach()
        es_config = configsets.Elasticsearch(self.bucket, self.bucket_key_prefix)
        ls_config = configsets.Logstash(self.bucket, self.bucket_key_prefix)
        return cf.Init(
            cf.InitConfigSets(
                elasticsearch=['network_attach', 'es_config'],
                logstash=['ls_config']
            ),
            network_attach=network_config.config(),
            es_config=es_config.config(),
            ls_config=ls_config.config()
        )

    # TODO: it seems we could do a better job tying these names into the above method.
    def _es_configset_names(self):
        return ['elasticsearch', 'logstash']

    def create_kibana(self):
        sg = self._create_kibana_sg()
        iam_profile = self._create_kibana_iam_profile()
        self._create_kibana_asg(sg, iam_profile)

    def _create_kibana_sg(self):
        ingress_rules = [
            net.sg_rule(net.CIDR_ANY, port, net.TCP) for port in (80, 443)
        ] + [
            net.sg_rule(self.vpc_cidr, 22, net.TCP)  # SSH. Remove if you don't need it.
        ]
        kibana_sg = ec2.SecurityGroup('KibanaSecurityGroup',
                                      GroupDescription='SecurityGroup for Kibana',
                                      SecurityGroupIngress=ingress_rules,
                                      VpcId=self.vpc_id,
                                      Tags=self.default_tags)
        self.add_resource(kibana_sg)
        self.output_ref('KibanaSG', kibana_sg)
        return kibana_sg

    def _create_kibana_iam_profile(self):
        policy = iam.Policy(
            PolicyName='KibanaInstance',
            PolicyDocument={
                'Statement': [{
                    'Effect': 'Allow',
                    'Resource': ['*'],
                    'Action': ['ec2:Attach*', 'ec2:Describe*']
                }, {
                    'Effect': 'Allow',
                    'Resource': 'arn:aws:s3:::{}/*'.format(self.bucket),
                    'Action': ['s3:Get*']
                }]
            })
        role = iam.Role('KibanaInstanceRole',
                        AssumeRolePolicyDocument=service_role_policy_doc.ec2,
                        Policies=[policy])
        profile = iam.InstanceProfile('KibanaInstanceProfile',
                                      Path='/',
                                      Roles=[tp.Ref(role)])
        self.add_resources(role, profile)
        return profile

        return None

    def _create_kibana_asg(self, sg, iam_profile):
        asg_name = 'KibanaASG'
        user_data = self._create_kibana_userdata(asg_name, self.es_eni)  # TODO: this implicit instance variable is icky
        lc = asg.LaunchConfiguration('KibanaLC',
                                     ImageId=tp.FindInMap(AMI_REGION_MAP_NAME, self.region, 'KIBANA'),
                                     InstanceType=self.kibana_instance_type,
                                     SecurityGroups=[tp.Ref(sg)],
                                     KeyName=tp.Ref(self.SERVER_KEY_PARM_NAME),
                                     IamInstanceProfile=tp.Ref(iam_profile),
                                     InstanceMonitoring=False,
                                     AssociatePublicIpAddress=True,  # TODO: point to an ELB or Route53 entry instead?
                                     UserData=user_data)
        group = asg.AutoScalingGroup(asg_name,
                                     MinSize=1,
                                     MaxSize=1,
                                     LaunchConfigurationName=tp.Ref(lc),
                                     VPCZoneIdentifier=self.kibana_subnet_ids,
                                     Tags=asgtag(self._rename('{} Kibana')))
        group.Metadata = self._create_kibana_metadata()

        self.add_resources(lc, group)
        self.output(group)

    def _create_kibana_userdata(self, asg_name, es_eni):
        startup = self._common_userdata() \
                  + UserDataSegments.eni_to_ip(es_eni, '/tmp/es_network_host') \
                  + UserDataSegments.invoke_cfn_init(asg_name, self._kibana_configset_names())
        return tp.Base64(tp.Join('', startup))

    def _create_kibana_metadata(self):
        return cf.Metadata(
            self._create_kibana_cf_init()
        )

    # TODO: it seems we could do a better job tying these into the configset names.
    def _create_kibana_cf_init(self):
        kib_config = configsets.Kibana(self.bucket, self.bucket_key_prefix)
        return cf.Init(
            cf.InitConfigSets(
                kibana=['kibana_config']
            ),
            kibana_config=kib_config.config()
        )

    def _kibana_configset_names(self):
        return ['kibana']

    def _common_userdata(self):
        return UserDataSegments.preamble() \
            + UserDataSegments.install_elastic_repos() \
            + UserDataSegments.install_apt_packages() \
            + UserDataSegments.install_cfn_init()


if __name__ == '__main__':
    t = TinyElkTemplate('Testing',
                        region='us-west-2',
                        bucket='my_bucket',
                        bucket_key_prefix='my_bucket_prefix',
                        vpc_id='vpc-deadbeef',
                        vpc_cidr='10.0.0.0/16',
                        es_subnet_id='subnet-deadbeef',
                        kibana_subnet_ids=['subnet-cab4abba'],
                        description='Testing')
    t.build_template()
    print(t.to_json())
