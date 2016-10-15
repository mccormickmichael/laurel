

class ESInitConfig(object):

    def packages(self):
        return {
            'rpm': {
                'elasticsearch': 'https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/rpm/elasticsearch/2.4.1/elasticsearch-2.4.1.rpm'  # TODO: abstract version number
            },
            'python': {
                'botocore': ['1.4.60'],
                'boto3': ['1.4.1']
            }
        }

    def files(self):
        return {
            '/etc/elasticsearch/elasticsearch.yml': {
                'group': 'elasticsearch',
                'owner': 'elasticsearch',
                'mode': '000777',
                'content': '''
bootstrap.memory_lock: true
network.host: _eth0_
cluster.name: tiny-elk
node.name: ${HOSTNAME}
'''
            }
        }

    def services(self):
        return {
              'sysvinit': {
                  'elasticsearch': {
                      'enabled': True,
                      'ensureRunning': True,
                      'files': ['/etc/elasticsearch/elasticsearch.yml']
                  }
              }
        }


class LogstashInitConfig(object):

    def __init__(self, bucket_name, key_prefix):
        self.bucket_name = bucket_name
        self.key_prefix = key_prefix

    def _to_s3_url(self, suffix):
        return 'http://{}.s3.amazonaws.com/{}/{}'.format(self.bucket_name, self.key_prefix, suffix)

    def packages(self):
        return {
            'rpm': {
                # Will this work on Amazon Linux? Apparently, yes.
                'logstash': 'https://download.elastic.co/logstash/logstash/packages/centos/logstash-2.4.0.noarch.rpm'
                # TODO: abstract version number?
            },
            'python': {
                'botocore': ['1.4.60'],
                'boto3': ['1.4.1']
            }
        }

    def files(self):
        return {
            '/etc/logstash/logstash.pre.conf': {
                'source': self._to_s3_url('ls-tiny.conf'),
                'group': 'logstash',
                'owner': 'logstash',
                'mode': '000777'  # TODO: change to 644
            },
            '/etc/logstash/ls_config.py': {
                'source': self._to_s3_url('ls_config.py'),
                'group': 'logstash',
                'owner': 'logstash',
                'mode': '000777'  # TODO: change to 644
            }
        }

    def commands(self):
        return {
            'config-logstash': {
                'command': 'python ls_config.py logstash.pre.conf',
                'cwd': '/etc/logstash'
            }
        }

    def services(self):
        return {
              'sysvinit': {
                  'logstash': {
                      'enabled': False,
                      'ensureRunning': True,
                      # 'files': ['/etc/elasticsearch/elasticsearch.yml']
                  }
              }
        }
