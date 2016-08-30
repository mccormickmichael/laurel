#!/usr/bin/python

# Define a stack to host a Consul cluster.
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
# - server_subnet_ids
#   List of subnets in which the consul server cluster should be built.
# - ui_subnet_ids
#   List of subnets in which the consul ui cluster should be built.
# - server_cluster_size
#   How many instances should participate in the cluster? Should be at least 3.
# - server_instance_type
#   Instance type of the server instances. Defaults to t2.micro
# - ui_instance_type
#   Instance type of the ui instances. Defaults to t2.micro
#
# Stack Parameters (provided to the template at stack create/update time):
#
# - ConsulKey
#   Name of the key pair to use to connect to Consul cluster server instances
#
# Stack Outputs:
#
# - Consul{N}ASG
#   ID of the autoscaling group controlling the Nth cluster member
# - Consul{N}ENI
#   ID of the elastic network interface attached to the Nth cluster member

import troposphere.ec2 as ec2
import troposphere.iam as iam
import troposphere.autoscaling as asg
import troposphere.cloudformation as cf
import troposphere.cloudwatch as cw
import troposphere.logs as logs
import troposphere as tp

from ..template import asgtag, TemplateBuilder, AMI_REGION_MAP_NAME, REF_STACK_NAME
from ..network import net


class ConsulTemplate(TemplateBuilder):

    BUILD_PARM_NAMES = ['vpc_id', 'vpc_cidr', 'server_subnet_ids', 'ui_subnet_ids', 'server_cluster_size',
                        'server_instance_type', 'ui_instance_type']
    CONSUL_KEY_PARAM_NAME = 'ConsulKey'

    def __init__(self, name,
                 region,
                 bucket,
                 key_prefix,
                 vpc_id,
                 vpc_cidr,
                 server_subnet_ids,
                 ui_subnet_ids=(),
                 description='[REPLACEME]',
                 server_cluster_size=3,
                 server_instance_type='t2.micro',
                 ui_instance_type='t2.micro'):
        super(ConsulTemplate, self).__init__(name, description, ConsulTemplate.BUILD_PARM_NAMES)

        self.region = region
        self.bucket = bucket
        self.key_prefix = key_prefix
        self.vpc_id = vpc_id
        self.vpc_cidr = vpc_cidr
        self.server_subnet_ids = list(server_subnet_ids)
        self.ui_subnet_ids = list(ui_subnet_ids)
        self.server_cluster_size = int(server_cluster_size)
        self.server_instance_type = server_instance_type
        self.ui_instance_type = ui_instance_type

    def internal_build_template(self):
        self.create_parameters()

        self.create_logstreams()

        self.create_consul_sg()
        self.create_server_cluster()
        if len(self.ui_subnet_ids) > 0:
            self.create_ui_cluster()

    def create_server_cluster(self):
        server_sg = self.create_server_sg()
        self.iam_profile = self.create_server_iam_profile()
        server_subnet_len = len(self.server_subnet_ids)
        self.server_enis = [
            self.create_server_eni(i, self.server_subnet_ids[i % server_subnet_len])
            for i in range(self.server_cluster_size)
        ]
        self.server_asgs = [
            self.create_server_asg(i, server_sg, self.iam_profile,
                                   self.server_subnet_ids[i % server_subnet_len], self.server_enis[i])
            for i in range(self.server_cluster_size)
        ]
        self.server_asgs[0].Metadata = self._create_server_metadata()

    def create_ui_cluster(self):
        self.ui_sg = self.create_ui_sg()
        self.ui_asg = self.create_ui_asg(self.ui_sg, self.iam_profile)

    def create_parameters(self):
        self.add_parameter(tp.Parameter(self.CONSUL_KEY_PARAM_NAME, Type='String'))

    def create_server_eni(self, index, subnet_id):
        eni = ec2.NetworkInterface('Consul{}ENI'.format(index),
                                   Description='ENI for Consul cluster member {}'.format(index),
                                   GroupSet=[tp.Ref(self.consul_sg)],
                                   SourceDestCheck=True,
                                   SubnetId=subnet_id,
                                   Tags=self._rename('{} ENI-'+str(index)))
        self.add_resource(eni)
        self.output(eni)
        return eni

    def create_server_sg(self):
        rules = [
            net.sg_rule(self.vpc_cidr, net.SSH, net.TCP)
        ]

        sg = ec2.SecurityGroup('ConsulServerSecurityGroup',
                               GroupDescription='Consul Server Instance Security Group',
                               SecurityGroupIngress=rules,
                               VpcId=self.vpc_id,
                               Tags=self.default_tags)
        self.add_resource(sg)
        return sg

    def create_server_asg(self, index, instance_sg, iam_profile, subnet_id, eni):
        lc_name = self._server_lc_name(index)
        lc = asg.LaunchConfiguration(lc_name,
                                     ImageId=tp.FindInMap(AMI_REGION_MAP_NAME, self.region, 'GENERAL'),
                                     InstanceType=self.server_instance_type,
                                     SecurityGroups=[tp.Ref(instance_sg)],
                                     KeyName=tp.Ref(self.CONSUL_KEY_PARAM_NAME),
                                     IamInstanceProfile=tp.Ref(iam_profile),
                                     InstanceMonitoring=False,
                                     AssociatePublicIpAddress=False,
                                     UserData=self._create_server_userdata(eni, index))
        group = asg.AutoScalingGroup(self._server_asg_name(index),
                                     MinSize=1, MaxSize=1,
                                     LaunchConfigurationName=tp.Ref(lc),
                                     VPCZoneIdentifier=[subnet_id],
                                     Tags=asgtag(self._rename('{} Server-'+str(index))))
        self.add_resources(lc, group)
        self.output(group)
        return group

    def _server_lc_name(self, index):
        return 'Consul{}LC'.format(index)

    def _server_asg_name(self, index):
        return 'Consul{}ASG'.format(index)

    def create_consul_sg(self):
        # see https://www.consul.io/docs/agent/options.html#ports-used
        ingress_rules = [
            net.sg_rule(self.vpc_cidr, port, net.TCP) for port in (53, (8300, 8302), 8400, 8500, 8600)
        ] + [
            net.sg_rule(self.vpc_cidr, port, net.UDP) for port in ((8301, 8302), 8600)
        ]
        self.consul_sg = ec2.SecurityGroup('ConsulAgentSecurityGroup',
                                           GroupDescription='Security group for Cosul Agents',
                                           SecurityGroupIngress=ingress_rules,
                                           VpcId=self.vpc_id,
                                           Tags=self.default_tags)
        self.add_resource(self.consul_sg)
        self.output_ref('ConsulAgentSG', self.consul_sg)

    def create_ui_sg(self):
        ingress_rules = [
            net.sg_rule(net.CIDR_ANY, port, net.TCP) for port in [net.HTTP, net.HTTPS]
        ] + [
            net.sg_rule(self.vpc_cidr, net.SSH, net.TCP)
        ]
        # egress_rules = []  # TODO: egress should only talk to private subnets over specified ports,
        #                            and to everyone over ephemeral ports
        sg = ec2.SecurityGroup('ConsulUISecurityGroup',
                               GroupDescription='Consul UI Server Security Group',
                               SecurityGroupIngress=ingress_rules,
                               VpcId=self.vpc_id,
                               Tags=self.default_tags)
        self.add_resource(sg)
        return sg

    def create_ui_asg(self, instance_sg, iam_profile):
        lc = asg.LaunchConfiguration('ConsulUILC',
                                     ImageId=tp.FindInMap(AMI_REGION_MAP_NAME, self.region, 'GENERAL'),
                                     InstanceType=self.ui_instance_type,
                                     SecurityGroups=[tp.Ref(self.consul_sg), tp.Ref(instance_sg)],
                                     KeyName=tp.Ref(self.CONSUL_KEY_PARAM_NAME),
                                     IamInstanceProfile=tp.Ref(iam_profile),
                                     InstanceMonitoring=False,
                                     AssociatePublicIpAddress=True,  # TODO: Do we need this if we are behind an ELB?
                                     UserData=self._create_ui_userdata())
        group = asg.AutoScalingGroup('ConsulUIASG',
                                     MinSize=1, MaxSize=2,
                                     LaunchConfigurationName=tp.Ref(lc),
                                     Cooldown=600,
                                     HealthCheckGracePeriod=600,
                                     HealthCheckType='EC2',  # TODO: switch to ELB
                                     TerminationPolicies=['OldestLaunchConfiguration', 'OldestInstance'],
                                     # LoadBalancerNames=...  # TODO
                                     VPCZoneIdentifier=self.ui_subnet_ids,
                                     Tags=asgtag(self._rename('{} UI')))
        scale_out = asg.ScalingPolicy('ConsulUIScaleOutPolicy',
                                      AutoScalingGroupName=tp.Ref(group),
                                      AdjustmentType='ChangeInCapacity',
                                      Cooldown=600,
                                      PolicyType='SimpleScaling',
                                      ScalingAdjustment=1)
        scale_in = asg.ScalingPolicy('ConsulUIScaleInPolicy',
                                     AutoScalingGroupName=tp.Ref(group),
                                     AdjustmentType='ChangeInCapacity',
                                     Cooldown=600,
                                     PolicyType='SimpleScaling',
                                     ScalingAdjustment=-1)
        # TODO: better metrics, like response time or something
        scale_out_alarm = cw.Alarm('ConsulUIScaleOutAlarm',
                                   ActionsEnabled=True,
                                   AlarmActions=[tp.Ref(scale_out)],
                                   AlarmDescription='Scale out ConsulUIASG when instance CPU exceeds 50% for 15 minutes',
                                   ComparisonOperator='GreaterThanThreshold',
                                   Dimensions=[cw.MetricDimension(Name='AutoScalingGroupName', Value=tp.Ref(group))],
                                   EvaluationPeriods=3,
                                   MetricName='CPUUtilization',
                                   Namespace='AWS/EC2',
                                   Period=300,
                                   Statistic='Average',
                                   Threshold='50',
                                   Unit='Percent')
        scale_in_alarm = cw.Alarm('ConsulUIScaleInAlarm',
                                  ActionsEnabled=True,
                                  AlarmActions=[tp.Ref(scale_in)],
                                  AlarmDescription='Scale in ConsulUIASG when instance CPU < 25% for 15 minutes',
                                  ComparisonOperator='LessThanThreshold',
                                  Dimensions=[cw.MetricDimension(Name='AutoScalingGroupName', Value=tp.Ref(group))],
                                  EvaluationPeriods=3,
                                  MetricName='CPUUtilization',
                                  Namespace='AWS/EC2',
                                  Period=300,
                                  Statistic='Average',
                                  Threshold='25',
                                  Unit='Percent')
        self.add_resources(lc, group, scale_out, scale_in, scale_out_alarm, scale_in_alarm)
        self.output(group)
        return group

    def create_logstreams(self):
        self.log_group = logs.LogGroup('ConsulLogGroup',
                                       RetentionInDays=3)
        self.add_resources(self.log_group)

    def create_server_iam_profile(self):
        role = iam.Role('ConsulInstanceRole',
                        AssumeRolePolicyDocument={
                            'Statement': [{
                                'Effect': 'Allow',
                                'Principal': {'Service': ['ec2.amazonaws.com']},
                                'Action': ['sts:AssumeRole']
                            }]
                        },
                        Policies=[
                            iam.Policy(
                                PolicyName='ConsulInstance',
                                PolicyDocument={
                                    'Statement': [{
                                        'Effect': 'Allow',
                                        'Resource': ['*'],
                                        'Action': ['ec2:Attach*', 'ec2:Describe*']
                                    }, {
                                        'Effect': 'Allow',
                                        'Resource': 'arn:aws:s3:::{}/*'.format(self.bucket),
                                        'Action': ['s3:Get*']
                                    }, {
                                        'Effect': 'Allow',
                                        'Resource': 'arn:aws:logs:{}:*:*'.format(self.region),
                                        'Action': [
                                            'logs:CreateLogGroup',
                                            'logs:CreateLogStream',
                                            'logs:PutLogEvents',
                                            'logs:DescribeLogStreams'
                                        ]
                                    }]
                                }
                            )
                        ])
        profile = iam.InstanceProfile('ConsulInstanceProfile',
                                      Path='/',
                                      Roles=[tp.Ref(role)])
        self.add_resources(role, profile)
        return profile

    def _create_server_userdata(self, eni, cluster_index):
        resource_name = self._server_asg_name(0)
        startup = [
            '#!/bin/bash\n',
            'yum update -y && yum install -y yum-cron && chkconfig yum-cron on\n',
            'REGION=', self.region, '\n',
            'ENI_ID=', tp.Ref(eni), '\n',
            'INS_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)\n'
            # TODO: do we need a sleep/check loop here? It hasn't failed so far
            'aws ec2 attach-network-interface --instance-id $INS_ID --device-index 1 --network-interface-id $ENI_ID --region $REGION\n',
            'mkdir -p -m 0755 /opt/consul\n'
            'echo "', cluster_index, '" > /opt/consul/cluster_index\n',
            'echo $ENI_ID > /opt/consul/eni_id\n',
            '/opt/aws/bin/cfn-init -v ',
            '  --stack ', REF_STACK_NAME,
            '  --resource ', resource_name,
            '  --configsets install_server',
            '  --region $REGION\n',
        ]
        return tp.Base64(tp.Join('', startup))  # TODO: There has GOT to be a better way to do userdata.

    def _create_ui_userdata(self):
        resource_name = self._server_asg_name(0)
        startup = [
            '#!/bin/bash\n',
            'yum update -y && yum install -y yum-cron && chkconfig yum-cron on\n',
            'REGION=', self.region, '\n',
            'mkdir -p -m 0755 /opt/consul\n'
            '/opt/aws/bin/cfn-init -v ',
            '  --stack ', REF_STACK_NAME,
            '  --resource ', resource_name,
            '  --configsets install_ui',
            '  --region $REGION\n',
        ]
        return tp.Base64(tp.Join('', startup))  # TODO: There has GOT to be a better way to do userdata.

    def _create_server_metadata(self):
        return cf.Metadata(
            cf.Init(
                cf.InitConfigSets(
                    install_server=['install', 'config_server', 'startup'],
                    install_ui=['install', 'config_ui', 'startup']),
                install=self._create_install_initconfig(),
                startup=self._create_startup_initconfig(),
                config_server=self._create_config_server_initconfig(),
                config_ui=self._create_config_ui_initconfig()
            ))

    def _get_consul_dir(self):
        return '/opt/consul'

    def _get_config_consul_py(self):
        return '{}/config_consul.py'.format(self._get_consul_dir())

    def _get_consul_config_file(self):
        return '{}/config/config.json'.format(self._get_consul_dir())

    def _get_consul_data_dir(self):
        return '{}/data'.format(self._get_consul_dir())

    def _get_consul_agent_dir(self):
        return '{}/agent'.format(self._get_consul_dir())

    def _get_consul_ui_dir(self):
        return '{}/ui'.format(self._get_consul_dir())

    def _get_consul_source_prefix(self):
        return 'http://{}.s3.amazonaws.com/{}'.format(self.bucket, self.key_prefix)

    def _create_install_initconfig(self):
        config_consul_py = self._get_config_consul_py()
        consul_agent_dir = self._get_consul_agent_dir()
        source_prefix = self._get_consul_source_prefix()
        return cf.InitConfig(
            packages={
                'python': {
                    'boto3': []
                }
            },
            # groups={}, # do we need a consul group?
            # users={}, # do we need a consul user?
            sources={
                consul_agent_dir: 'https://releases.hashicorp.com/consul/0.6.3/consul_0.6.3_linux_amd64.zip'
            },
            files={
                config_consul_py: {
                    'source': '{}/config_consul.py'.format(source_prefix),
                    'mode': '000755',
                    'owner': 'root',
                    'group': 'root'
                },
                '/etc/init.d/consul': {
                    'source': '{}/consul.service'.format(source_prefix),
                    'mode': '000755',
                    'owner': 'root',
                    'group': 'root'
                },
            },
            commands={
                '20_mode': {
                    'command': 'chmod 755 {}/consul'.format(consul_agent_dir)
                },
            }
        )

    def _create_startup_initconfig(self):
        config_consul_py = self._get_config_consul_py()
        consul_config_file = self._get_consul_config_file()
        consul_data_dir = self._get_consul_data_dir()
        consul_agent_dir = self._get_consul_agent_dir()
        return cf.InitConfig(
            commands={
                '10_dirs': {
                    'command': 'mkdir -m 0755 -p {}'.format(consul_data_dir)
                },
                '30_consul_config': {
                    'command': 'python {0} {1}'.format(config_consul_py, consul_config_file)
                },
                '50_chkconfig': {
                    'command': 'chkconfig --add consul'
                }
            },
            services={
                'sysvinit': {
                    'consul': {
                        'enabled': 'true',
                        'ensureRunning': 'true',
                        'files': [consul_config_file],
                        'sources': [consul_agent_dir],
                        'commands': 'config'
                    }
                },
            }
        )

        return None

    def _create_config_server_initconfig(self):
        cwlogs_config_file = '/opt/cw-logs/cwlogs.cfg'
        config_cwlogs_py = '/opt/cw-logs/cwlogs.py'
        consul_config_file = self._get_consul_config_file()
        consul_data_dir = self._get_consul_data_dir()
        source_prefix = self._get_consul_source_prefix()
        return cf.InitConfig(
            files={
                # See https://www.consul.io/docs/agent/options.html#configuration_files
                consul_config_file: {
                    'content': {
                        'datacenter': self.region,
                        'data_dir': consul_data_dir,
                        'log_level': 'INFO',
                        'server': True,
                        'bootstrap_expect': self.server_cluster_size,
                        'bind_addr': 'REPLACE AT RUNTIME',
                        'retry_join': 'REPLACE AT RUNTIME',
                        '_eni_ids': [tp.Ref(e) for e in self.server_enis]  # used for runtime resolution
                    },
                    'mode': '000755',
                    'owner': 'root',  # could be consul user?
                    'group': 'root'   # could be consul group?
                },
                '/opt/cw-logs/awslogs-agent-setup.py': {
                    'source': 'https://s3.amazonaws.com/aws-cloudwatch/downloads/latest/awslogs-agent-setup.py',
                    'mode': '000755',
                    'owner': 'root',
                    'group': 'root'
                },
                cwlogs_config_file: {
                    'content': tp.Join('', [
                        '[general]\n',
                        'state_file = /var/awslogs/state/agent-state\n',
                        '\n',
                        '[consul_agent]\n',
                        'file = /var/log/consul\n',
                        'datetime_format = %b %d %H:%M:%S\n',
                        'log_group_name = ', tp.Ref(self.log_group), '\n',
                        'log_stream_name = REPLACE_AT_RUNTIME\n'
                    ]),
                    'mode': '000755',
                    'owner': 'root',
                    'group': 'root'
                },
                config_cwlogs_py: {
                    'source': '{}/config_cwlogs.py'.format(source_prefix),
                    'mode': '000755',
                    'owner': 'root',
                    'group': 'root'
                }

            },
            commands={
                '31_cwlogs_config': {
                    'command': 'python {0} {1}'.format(config_cwlogs_py, cwlogs_config_file)
                },
                '40_wait': {
                    'command': 'while [ `ifconfig | grep "inet addr" | wc -l` -lt 3 ]; do echo "waiting for ip addr" >> /opt/consul/wait && sleep 2; done'
                },
                '60_cwlogs': {
                    'command': 'python /opt/cw-logs/awslogs-agent-setup.py -n -r {} -c {}'.format(self.region, cwlogs_config_file)
                },

            }
        )

    def _create_config_ui_initconfig(self):
        ui_dir = self._get_consul_ui_dir()
        consul_config_file = self._get_consul_config_file()
        consul_data_dir = self._get_consul_data_dir()
        return cf.InitConfig(
            sources={
                ui_dir: 'https://releases.hashicorp.com/consul/0.6.3/consul_0.6.3_web_ui.zip'
            },
            files={
                # See https://www.consul.io/docs/agent/options.html#configuration_files
                consul_config_file: {
                    'content': {
                        'addresses': {
                            'http': '0.0.0.0'
                        },
                        'datacenter': self.region,
                        'data_dir': consul_data_dir,
                        'log_level': 'INFO',
                        'retry_join': 'REPLACE AT RUNTIME',
                        'ports': {
                            'http': 80
                        },
                        'ui': True,
                        'ui_dir': ui_dir,
                        '_eni_ids': [tp.Ref(e) for e in self.server_enis]  # used for runtime resolution
                    },
                    'mode': '000755',
                    'owner': 'root',  # could be consul user?
                    'group': 'root'   # could be consul group?
                }
            }
        )


if __name__ == '__main__':
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else 'Test'
    region = sys.argv[2] if len(sys.argv) > 2 else 'us-west-2'
    bucket = sys.argv[3] if len(sys.argv) > 3 else 'thousandleaves-us-west-2-laurel-deploy'
    vpc_id = sys.argv[4] if len(sys.argv) > 4 else 'vpc-deadbeef'
    vpc_cidr = sys.argv[5] if len(sys.argv) > 5 else '10.0.0.0/16'
    server_subnet_ids = sys.argv[6:] if len(sys.argv) > 6 else ['subnet-deadbeef', 'subnet-cab4abba']
    ui_subnet_ids = server_subnet_ids
    key_prefix = 'scaffold/consul-YYYYMMDD-HHmmss'

    template = ConsulTemplate(name, region, bucket, key_prefix, vpc_id, vpc_cidr, server_subnet_ids, ui_subnet_ids)
    template.build_template()
    print template.to_json()
