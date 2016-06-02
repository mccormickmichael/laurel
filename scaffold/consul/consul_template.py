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

    BUILD_PARM_NAMES = ['region', 'bucket', 'vpc_id', 'vpc_cidr', 'server_subnet_ids', 'ui_subnet_ids',
                        'server_cluster_size', 'server_instance_type', 'ui_instance_type']
    CONSUL_KEY_PARAM_NAME = 'ConsulKey'

    def __init__(self, name,
                 region,
                 bucket,
                 vpc_id,
                 vpc_cidr,
                 server_subnet_ids,
                 ui_subnet_ids=[],
                 description='[REPLACEME]',
                 server_cluster_size=3,
                 server_instance_type='t2.micro',
                 ui_instance_type='t2.micro'):
        super(ConsulTemplate, self).__init__(name, description, ConsulTemplate.BUILD_PARM_NAMES)

        self.region = region
        self.bucket = bucket
        self.vpc_id = vpc_id
        self.vpc_cidr = vpc_cidr
        self.server_subnet_ids = server_subnet_ids
        self.ui_subnet_ids = ui_subnet_ids
        self.server_cluster_size = server_cluster_size
        self.server_instance_type = server_instance_type
        self.ui_instance_type = ui_instance_type

    def build_template(self):
        super(ConsulTemplate, self).build_template()

        self.create_parameters()

        self.create_logstreams()

        self.create_server_cluster()
        if len(self.ui_subnet_ids) > 0:
            self.create_ui_cluster()

    def create_server_cluster(self):
        sg = self.create_server_sg()
        iam_profile = self.create_server_iam_profile()
        server_subnet_len = len(self.server_subnet_ids)
        self.server_enis = [
            self.create_server_eni(i, sg, self.server_subnet_ids[i % server_subnet_len])
            for i in range(self.server_cluster_size)
        ]
        self.server_asgs = [
            self.create_server_asg(i, sg, iam_profile, self.server_subnet_ids[i % server_subnet_len], self.server_enis[i])
            for i in range(self.server_cluster_size)
        ]
        self.server_asgs[0].Metadata = self._create_server_metadata()

    def create_ui_cluster(self):
        sg = self.create_ui_sg()
        iam_profile = self.create_ui_iam_profile()
        self.ui_asg = self.create_ui_asg(sg, iam_profile)

    def create_parameters(self):
        self.add_parameter(tp.Parameter(self.CONSUL_KEY_PARAM_NAME, Type='String'))

    def create_server_eni(self, index, security_group, subnet_id):
        eni = ec2.NetworkInterface('Consul{}ENI'.format(index),
                                   Description='ENI for Consul cluster member {}'.format(index),
                                   GroupSet=[tp.Ref(security_group)],
                                   SourceDestCheck=True,
                                   SubnetId=subnet_id,
                                   Tags=self._rename('{} ENI-'+str(index)))
        self.add_resource(eni)
        self.add_output(tp.Output(eni.name, Value=tp.Ref(eni)))
        return eni

    def create_server_sg(self):
        rules = [net.sg_rule(self.vpc_cidr, net.SSH, net.TCP)] + [
            net.sg_rule(self.vpc_cidr, ports, protocol)
            for protocol in [net.TCP, net.UDP] for ports in [53, (8300, 8302), 8400, 8500, 8600]
        ]
        sg = ec2.SecurityGroup('ConsulSecurityGroup',
                               GroupDescription='Consul Instance Security Group',
                               SecurityGroupIngress=rules,
                               VpcId=self.vpc_id,
                               Tags=self.default_tags)
        self.add_resource(sg)
        return sg

    def create_server_asg(self, index, security_group, iam_profile, subnet_id, eni):
        lc_name = self._server_lc_name(index)
        lc = asg.LaunchConfiguration(lc_name,
                                     ImageId=tp.FindInMap(AMI_REGION_MAP_NAME, self.region, 'GENERAL'),
                                     InstanceType=self.server_instance_type,
                                     SecurityGroups=[tp.Ref(security_group)],
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
        self.add_output(tp.Output(group.name, Value=tp.Ref(group)))
        return group

    def create_ui_asg(self, security_group, iam_profile):
        return None

    def _server_lc_name(self, index):
        return 'Consul{}LC'.format(index)

    def _server_asg_name(self, index):
        return 'Consul{}ASG'.format(index)

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
                                        'Action': ['ec2:Attach*', 'ec2:Describe*', 's3:*']
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
            '  --configsets install',
            '  --region $REGION\n',
        ]
        return tp.Base64(tp.Join('', startup))  # TODO: There has GOT to be a better way to do userdata.

    def _create_server_metadata(self):
        consul_dir = '/opt/consul'
        agent_dir = '{}/agent'.format(consul_dir)
        ui_dir = '{}/ui'.format(consul_dir)
        config_dir = '{}/config'.format(consul_dir)
        data_dir = '{}/data'.format(consul_dir)

        server_config_file = '{}/config.json'.format(config_dir)
        # ui_config_file = '{}/config_ui.json'.format(config_dir) ??
        config_server_py = '{}/config_server.py'.format(consul_dir)
        # config_ui_py = '{}/config_ui.py'.format(consul_dir)

        cwlogs_config_file = '/opt/cw-logs/cwlogs.cfg'
        config_cwlogs_py = '/opt/cw-logs/cwlogs.py'

        source_prefix = 'http://{}.s3.amazonaws.com/scaffold/consul'.format(self.bucket)

        return cf.Metadata(
            cf.Init(
                cf.InitConfigSets(install=['install']),
                install=cf.InitConfig(
                    packages={
                        'python': {
                            'boto3': []
                        }
                    },
                    # groups={}, # do we need a consul group?
                    # users={}, # do we need a consul user?
                    sources={
                        agent_dir: 'https://releases.hashicorp.com/consul/0.6.3/consul_0.6.3_linux_amd64.zip',
                        ui_dir: 'https://releases.hashicorp.com/consul/0.6.3/consul_0.6.3_web_ui.zip'
                    },
                    files={
                        # See https://www.consul.io/docs/agent/options.html#configuration_files
                        server_config_file: {
                            'content': {
                                'datacenter': self.region,
                                'data_dir': data_dir,
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
                        config_server_py: {
                            'source': '{}/config_server.py'.format(source_prefix),
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
                            'source': '{}/cwlogs.cfg'.format(source_prefix),
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
                        '10_dirs': {
                            'command': 'mkdir -m 0755 -p {}'.format(data_dir)
                        },
                        '20_mode': {
                            'command': 'chmod 755 {}/consul'.format(agent_dir)
                        },
                        '30_consul_config': {
                            'command': 'python {0} {1}'.format(config_server_py, server_config_file)
                        },
                        '31_cwlogs_config': {
                            'command': 'python {0} {1}'.format(config_cwlogs_py, cwlogs_config_file)
                        },
                        '40_wait': {
                            'command': 'while [ `ifconfig | grep "inet addr" | wc -l` -lt 3 ]; do echo "waiting for ip addr" > /opt/consul/wait && sleep 2; done'
                        },
                        '50_chkconfig': {
                            'command': 'chkconfig --add consul'
                        },
                        '60_cwlogs': {
                            'command': 'python /opt/cw-logs/awslogs-agent-setup.py -n -r {} -c /opt/cw-logs/cwlogs.cfg'.format(self.region)
                        }
                    },
                    services={
                        'sysvinit': {
                            'consul': {
                                'enabled': 'true',
                                'ensureRunning': 'true',
                                'files': [server_config_file],
                                'sources': [agent_dir],
                                'commands': 'config'
                            }
                        },
                        # dnsmasq?
                    }
                )
            )
        )


if __name__ == '__main__':
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else 'Test'
    region = sys.argv[2] if len(sys.argv) > 2 else 'us-west-2'
    bucket = sys.argv[3] if len(sys.argv) > 3 else 'thousandleaves-us-west-2-laurel-deploy'
    vpc_id = sys.argv[4] if len(sys.argv) > 4 else 'vpc-deadbeef'
    vpc_cidr = sys.argv[5] if len(sys.argv) > 5 else '10.0.0.0/16'
    server_subnet_ids = sys.argv[6:] if len(sys.argv) > 6 else ['subnet-deadbeef', 'subnet-cab4abba']

    template = ConsulTemplate(name, region, bucket, vpc_id, vpc_cidr, server_subnet_ids)
    template.build_template()
    print template.to_json()
