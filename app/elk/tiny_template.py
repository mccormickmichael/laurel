# Define a CloudFormation template to host a tiny ElasticSearch stack:
# 1 ElasticSearch server
# 1 Logstash indexing server
# 1 Kibana server
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
# - es_subnets
#   List of the subnet in which the Logstash/Elasticsearch server should be built.

# Don't know about the rest of these...

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

import troposphere as tp
import troposphere.autoscaling as asg
import troposphere.cloudformation as cf
import troposphere.ec2 as ec2
import troposphere.elasticloadbalancingv2 as elb2
import troposphere.iam as iam


from scaffold.cf.template import TemplateBuilder, asgtag, AMI_REGION_MAP_NAME, REF_REGION, REF_STACK_NAME
from scaffold.cf import net
from scaffold.cf import AmiRegionMap
from scaffold.iam import service_role_policy_doc

from .tiny_userdata import ESUserdata, LogstashUserdata
from .tiny_initconfig import ESInitConfig, LogstashInitConfig


AMI_REGION_MAP = {
    'us-east-1': {'ES': 'ami-60b6c60a', 'LOGSTASH': 'ami-60b6c60a', 'KIBANA': 'ami-60b6c60a'},
    'us-west-1': {'ES': 'ami-d5ea86b5', 'LOGSTASH': 'ami-d5ea86b5', 'KIBANA': 'ami-d5ea86b5'},
    'us-west-2': {'ES': 'ami-f0091d91', 'LOGSTASH': 'ami-f0091d91', 'KIBANA': 'ami-f0091d91'}
    # 'eu-west-1'
    # 'eu-central-1'
    # 'sa-east-1'
    # 'ap-southeast-1'
    # 'ap-southeast-2'
    # 'ap-northeast-1'
    # 'ap-northeast-2'
}


class TinyElkTemplate(TemplateBuilder):

    BUILD_PARM_NAMES = ['vpc_id', 'vpc_cidr', 'es_subnets']

    SERVER_KEY_PARM_NAME = 'ServerKey'

    def __init__(self, name,
                 region,
                 bucket,
                 bucket_key_prefix,
                 vpc_id,
                 vpc_cidr,
                 es_subnets,
                 create_logstash=False,
                 description='[REPLACEME]'):
        super(TinyElkTemplate, self).__init__(name, description, TinyElkTemplate.BUILD_PARM_NAMES)

        self.region = region
        self.bucket = bucket
        self.bucket_key_prefix = bucket_key_prefix
        self.vpc_id = vpc_id
        self.vpc_cidr = vpc_cidr
        self.es_subnets = es_subnets

    def internal_add_mappings(self):
        self.add_mapping(AMI_REGION_MAP_NAME, AmiRegionMap(AMI_REGION_MAP))

    def internal_build_template(self):
        self.create_parameters()

        self._create_common()

        self.create_elasticsearch()
        self.create_kibana()
        if self.create_logstash:
            self.create_logstash()

    def create_parameters(self):
        self.add_parameter(tp.Parameter(TinyElkTemplate.SERVER_KEY_PARM_NAME, Type='String'))

    def _create_common(self):
        self.ssh_sg = self._create_simple_sg('ElkSSHSecurityGroup', 'Security Group for accessing Elk stack instances', net.SSH)

    def _create_simple_sg(self, name, description, port_ranges):
        if type(port_ranges) is not list:
            port_ranges = [port_ranges]
        rules = [net.sg_rule(self.vpc_cidr, port, net.TCP) for port in port_ranges]
        sg = ec2.SecurityGroup(name,
                               GroupDescription=description,
                               SecurityGroupIngress=rules,
                               VpcId=self.vpc_id,
                               Tags=self.default_tags)
        self.add_resource(sg)
        return sg

    def create_elasticsearch(self):
        es_sg = self._create_es_sg()
        es_tg = self._create_es_target_group()
        self.es_elb = self._create_es_elb(es_tg)
        self._create_es_asg(es_sg, es_tg)

    def _create_es_sg(self):
        return self._create_simple_sg('ElasticsearchSecurityGroup', 'Security Group for Elasticsearch nodes', (9200, 9400))

    def _create_es_target_group(self):
        target_group = elb2.TargetGroup('ElasticsearchTargetGroup',
                                        HealthCheckIntervalSeconds=60,
                                        HealthCheckPath='/_cluster/health',
                                        HealthCheckPort=9200,
                                        HealthCheckProtocol='HTTP',
                                        HealthCheckTimeoutSeconds=5,
                                        HealthyThresholdCount=2,
                                        UnhealthyThresholdCount=2,
                                        Matcher=elb2.Matcher(HttpCode='200-299'),
                                        Name='ElasticsearchTiny',
                                        Port=9200,
                                        Protocol='HTTP',
                                        Tags=self.default_tags,
                                        VpcId=self.vpc_id)
        self.add_resource(target_group)
        return target_group

    def _create_es_elb(self, target_group):
        sg = ec2.SecurityGroup('ElasticsearchELBSecurityGroup',
                               GroupDescription='Security Group for the Elasticsearch ELB',
                               SecurityGroupIngress=[net.sg_rule(self.vpc_cidr, 9200, net.TCP)],
                               VpcId=self.vpc_id,
                               Tags=self.default_tags)
        elb = elb2.LoadBalancer('ElasticsearchELB',
                                Name='ElasticsearchTiny',
                                Scheme='internal',
                                SecurityGroups=[tp.Ref(sg)],
                                Subnets=self.es_subnets,
                                Tags=self.default_tags)
        listener = elb2.Listener('ElasticsearchELBListener',
                                 DefaultActions=[elb2.Action(TargetGroupArn=tp.Ref(target_group),
                                                             Type='forward')],
                                 LoadBalancerArn=tp.Ref(elb),
                                 Port=9200,
                                 Protocol='HTTP')
        self.add_resources(sg, elb, listener)
        self.output(elb)
        self.output_named('ElasticsearchDNSName', tp.GetAtt(elb.title, 'DNSName'))
        return elb

    def _create_es_asg(self, sg, target_group):
        asg_name = 'ElasticsearchASG'
        lc = asg.LaunchConfiguration('ElasticsearchLC',
                                     ImageId=tp.FindInMap(AMI_REGION_MAP_NAME, REF_REGION, 'ES'),
                                     InstanceType='t2.micro',  # TODO: how should we parameterize this?
                                     IamInstanceProfile=tp.Ref(self._create_es_iam_profile()),
                                     SecurityGroups=[tp.Ref(sg), tp.Ref(self.ssh_sg)],
                                     KeyName=tp.Ref(TinyElkTemplate.SERVER_KEY_PARM_NAME),
                                     InstanceMonitoring=False,
                                     AssociatePublicIpAddress=False,
                                     UserData=self._create_es_userdata(asg_name))
        group = asg.AutoScalingGroup(asg_name,
                                     MinSize=1,
                                     MaxSize=1,
                                     LaunchConfigurationName=tp.Ref(lc),
                                     TargetGroupARNs=[tp.Ref(target_group)],
                                     VPCZoneIdentifier=self.es_subnets,
                                     Tags=asgtag(self._rename('{} Elasticsearch')),
                                     Metadata=self._create_es_initconfig())
        self.add_resources(lc, group)
        self.output(group)
        return group

    def _create_es_iam_profile(self):
        role = iam.Role('ElasticsearchInstanceRole',
                        AssumeRolePolicyDocument=service_role_policy_doc.ec2,
                        Policies=[
                            iam.Policy(
                                PolicyName='ElasticsearchInstance',
                                PolicyDocument={
                                    'Statement': [{
                                        'Effect': 'Allow',
                                        'Resource': 'arn:aws:s3:::{}/*'.format(self.bucket),
                                        'Action': ['s3:Get*']
                                    }]
                                }
                            )
                        ])
        profile = iam.InstanceProfile('ElasticsearchInstanceProfile',
                                      Path='/',
                                      Roles=[tp.Ref(role)])
        self.add_resources(role, profile)
        return profile

    def _create_es_userdata(self, resource_name):
        items = ESUserdata(REF_STACK_NAME, resource_name, ['default'], REF_REGION).items()
        return tp.Base64(tp.Join('', items))

    def _create_es_initconfig(self):
        init = ESInitConfig()
        return cf.Init(
            cf.InitConfigSets(
                default=['elasticsearch']
            ),
            elasticsearch=cf.InitConfig(
                packages=init.packages(),
                files=init.files(),
                services=init.services()
            )
        )

    def create_logstash(self):
        ls_sg = self._create_ls_sg()
        ls_eni = self._create_ls_eni(ls_sg)
        self._create_ls_asg(ls_eni)

    def _create_ls_sg(self):
        return self._create_simple_sg('LogstashIndexSG', 'Security Group for Logstash indexing nodes', 5044)

    def _create_ls_eni(self, sg):
        eni = ec2.NetworkInterface('LogstashIndexENI',
                                   Description='ENI for the Logstash indexer',
                                   GroupSet=[tp.Ref(sg)],
                                   SourceDestCheck=True,
                                   SubnetId=self.es_subnets[0],  # TODO: is there a better way to allocate? I dunno.
                                   Tags=self.default_tags)
        self.add_resource(eni)
        self.output(eni)
        return eni

    def _create_ls_asg(self, eni):
        asg_name = 'LogstashIndexASG'
        lc = asg.LaunchConfiguration('LogstashIndexLC',
                                     ImageId=tp.FindInMap(AMI_REGION_MAP_NAME, REF_REGION, 'LOGSTASH'),
                                     InstanceType='t2.micro',  # TODO: how should we parameterize this?
                                     IamInstanceProfile=tp.Ref(self._create_ls_iam_profile()),
                                     SecurityGroups=[tp.Ref(self.ssh_sg)],
                                     KeyName=tp.Ref(TinyElkTemplate.SERVER_KEY_PARM_NAME),
                                     InstanceMonitoring=False,
                                     AssociatePublicIpAddress=False,
                                     UserData=self._create_ls_userdata(asg_name, eni))
        group = asg.AutoScalingGroup(asg_name,
                                     MinSize=1,
                                     MaxSize=1,
                                     LaunchConfigurationName=tp.Ref(lc),
                                     VPCZoneIdentifier=[eni.SubnetId],
                                     Tags=asgtag(self._rename('{} Logstash')),
                                     Metadata=self._create_ls_initconfig())
        self.add_resources(lc, group)
        self.output(group)
        return group

    def _create_ls_iam_profile(self):
        role = iam.Role('LogstashInstanceRole',
                        AssumeRolePolicyDocument=service_role_policy_doc.ec2,
                        Policies=[
                            iam.Policy(
                                PolicyName='LogstashInstance',
                                PolicyDocument={
                                    'Statement': [{
                                        'Effect': 'Allow',
                                        'Resource': 'arn:aws:s3:::{}/*'.format(self.bucket),
                                        'Action': ['s3:Get*']
                                    }, {
                                        'Effect': 'Allow',
                                        'Resource': '*',
                                        'Action': ['ec2:Attach*', 'ec2:Describe*']
                                    }]
                                }
                            )
                        ])
        profile = iam.InstanceProfile('LogstashInstanceProfile',
                                      Path='/',
                                      Roles=[tp.Ref(role)])
        self.add_resources(role, profile)
        return profile

    def _create_ls_userdata(self, resource_name, eni):
        userdata = LogstashUserdata(eni_id=tp.Ref(eni),
                                    es_host_ref=tp.GetAtt(self.es_elb.title, 'DNSName'),
                                    stack_ref=REF_STACK_NAME,
                                    resource_name=resource_name,
                                    configsets=['default'],
                                    region=REF_REGION)
        return tp.Base64(tp.Join('', userdata.items()))

    def _create_ls_initconfig(self):
        init = LogstashInitConfig(self.bucket, self.bucket_key_prefix)
        return cf.Init(
            cf.InitConfigSets(
                default=['logstash']
            ),
            logstash=cf.InitConfig(
                packages=init.packages(),
                files=init.files(),
                commands=init.commands(),
                services=init.services()
            )
        )

    def create_kibana(self):
        pass

if __name__ == '__main__':
    t = TinyElkTemplate('Testing',
                        region='us-west-2',
                        bucket='my_bucket',
                        bucket_key_prefix='my_bucket_prefix',
                        vpc_id='vpc-deadbeef',
                        vpc_cidr='10.0.0.0/16',
                        es_subnets=['subnet-deadbeef', 'subnet-cab4abba'],
                        create_logstash=False,
                        description='Testing')
    t.build_template()
    print(t.to_json())
