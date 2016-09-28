from scaffold.cf.template import REF_REGION, REF_STACK_NAME

import troposphere as tp

def endl(lines):
    return map(lambda l: l + '\n', lines)


class UserDataSegments(object):

    PREAMBLE = ['#!/bin/bash']

    INSTALL_APT_PACKAGES = ['apt-get -y update && apt-get -y upgrade',
                            'apt-get -y install awscli openjdk-7-jre-headless']

    INSTALL_CFN_INIT = ['wget -P /tmp https://bootstrap.pypa.io/ez_setup.py',
                        'python /tmp/ez_setup.py',
                        'wget -P /tmp https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz',
                        'easy_install /tmp/aws-cfn-bootstrap-latest.tar.gz']

    # TODO: Some of the repos specify particular versions of Elastic components.
    #       Consider extracting them to share withversions mentioned below
    INSTALL_ES_REPOS = ['wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | apt-key add -',
                        'echo "deb https://packages.elastic.co/elasticsearch/2.x/debian stable main" | tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list',
                        'echo "deb https://packages.elastic.co/logstash/2.4/debian stable main" | tee -a /etc/apt/sources.list',
                        'echo "deb https://packages.elastic.co/kibana/4.6/debian stable main" | tee -a /etc/apt/sources.list.d/kibana.list',
                        'echo "deb https://packages.elastic.co/beats/apt stable main" |  tee -a /etc/apt/sources.list.d/beats.list']

    @classmethod
    def preamble(cls):
        return endl(cls.PREAMBLE)

    @classmethod
    def install_apt_packages(cls):
        return endl(cls.INSTALL_APT_PACKAGES)

    @classmethod
    def install_cfn_init(cls):
        return endl(cls.INSTALL_CFN_INIT)

    @classmethod
    def install_elastic_repos(cls):
        return endl(cls.INSTALL_ES_REPOS)

    @classmethod
    def eni_to_ip(cls, eni, target_path):
        return ['aws ec2 describe-network-interfaces --network-interface-id ', tp.Ref(eni),
                ' --region ', REF_REGION,
                ' --query "NetworkInterfaces[0].PrivateIpAddress" > ', target_path, '\n']

    @classmethod
    def attach_eni(cls, eni):
        return ['ENI_ID=', tp.Ref(eni), '\n',
                'INS_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)\n',
                'aws ec2 attach-network-interface ',
                ' --instance-id $INS_ID ',
                ' --device-index 1 ',
                ' --network-interface-id $ENI_ID ',
                ' --region ', REF_REGION, '\n']

    @classmethod
    def invoke_cfn_init(cls, resource_name, config_sets):
        return ['/usr/local/bin/cfn-init -v',
                ' --stack ', REF_STACK_NAME,
                ' --resource ', resource_name,
                ' --configsets ', ','.join(config_sets),
                ' --region ', REF_REGION,
                '\n']


class ElasticSoftware(object):  # this terrible name is propagating. Also seriously unfinished

    LOGSTASH_VERSION = '2.4.0'
    SEARCH_VERISION = '2.4.0'
    KIBANA_VERSION = '4.6.1'
    FILEBEAT_VERSION = '1.3.1'
    # TODO: Other Beats clients

    ES_NAME = 'elasticsearch'
    LS_NAME = 'logstash'
    KB_NAME = 'kibana'
    FB_NAME = 'filebeat'

    ES_DEB_URL = 'https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.4.0/elasticsearch-2.4.0.deb'
    ES_ZIP_URL = 'https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/zip/elasticsearch/2.4.0/elasticsearch-2.4.0.zip'

    LS_DEB_URL = 'https://download.elastic.co/logstash/logstash/packages/debian/logstash-2.4.0_all.deb'
    LS_ZIP_URL = 'https://download.elastic.co/logstash/logstash/logstash-2.4.0.zip'

    KB_DEB_URL = 'https://download.elastic.co/kibana/kibana/kibana-4.6.1-amd64.deb'
    KB_LINUX_URL = 'https://download.elastic.co/kibana/kibana/kibana-4.6.1-linux-x86_64.tar.gz'

    FILEBEAT_DEB_URL = 'https://download.elastic.co/beats/filebeat/filebeat_1.3.1_amd64.deb'
    FILEBEAT_LINUX_URL = 'https://download.elastic.co/beats/filebeat/filebeat-1.3.1-x86_64.tar.gz'
    
    # TODO: see how this might actually be used.
