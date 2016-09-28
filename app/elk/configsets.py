import troposphere.cloudformation as cf


def s3_url_prefix(bucket, key_prefix):
    return 'http://{}.s3.amazonaws.com/{}'.format(bucket, key_prefix)


class NetworkInterfaceAttach(object):

    def config(self):
        return cf.InitConfig(
            files=self._files(),
            commands=self._commands())

    def _files(self):
        return {
            '/etc/network/interfaces.d/eth1.cfg': {
                'mode': '000755',
                'owner': 'root',
                'group': 'root',
                'content': '''auto eth1
iface eth1 inet dhcp'''
            }
        }

    def _commands(self):
        return {
            'eth1_up': {
                'command': 'ifup eth1'
            }
        }


class Elasticsearch(object):

    def __init__(self, bucket, key_prefix):
        self._s3_prefix = s3_url_prefix(bucket, key_prefix)

    def config(self):
        return cf.InitConfig(
            packages=self._packages(),
            files=self._files(),
            commands=self._commands(),
            services=self._services())

    def _packages(self):
        return {
            'apt': {
                'elasticsearch': []
            },
            'python': {
                'boto3': []
            }
        }

    def _files(self):
        return {
            '/etc/elasticsearch/es-tiny.yml': {
                'source': '{}/es-tiny.yml'.format(self._s3_prefix),
                'mode': '000777',
                'owner': 'elasticsearch',
                'group': 'elasticsearch'
            },
            '/etc/elasticsearch/es_config.py': {
                'source': '{}/es_config.py'.format(self._s3_prefix),
                'mode': '000777',
                'owner': 'elasticsearch',
                'group': 'elasticsearch'
            }
        }

    def _commands(self):
        return {
            'config_es': {
                'command': 'python es_config.py',
                'cwd': '/etc/elasticsearch'
            }
        }

    def _services(self):
        return {
            'sysvinit': {
                'elasticsearch': {
                    'enabled': True,
                    'ensureRunning': True
                }
            }
        }


class Logstash(object):
    def __init__(self, bucket, key_prefix):
        self._s3_prefix = s3_url_prefix(bucket, key_prefix)

    def config(self):
        return cf.InitConfig(
            packages=self._packages(),
            files=self._files(),
            commands=self._commands(),
            services=self._services())

    def _packages(self):
        return {
            'apt': {
                'logstash': []
            },
            'python': {
                'boto3': []
            }
        }

    def _files(self):
        return {
            '/etc/logstash/ls_conf.conf': {
                'source': '{}/logstash.conf'.format(self._s3_prefix),
                'mode': '000777',
                'owner': 'logstash',
                'group': 'logstash'
            },
            '/etc/logstash/ls_config.py': {
                'source': '{}/ls_config.py'.format(self._s3_prefix),
                'mode': '000777',
                'owner': 'logstash',
                'group': 'logstash'
            }
        }

    def _commands(self):
        return {
            'config_ls': {
                'command': 'python ls_config.py',
                'cwd': '/etc/logstash'
            }
        }

    def _services(self):
        return {
            'sysvinit': {
                'logstash': {
                    'enabled': True,
                    'ensureRunning': True
                }
            }
        }


class Kibana(object):
    def __init__(self, bucket, key_prefix):
        self._s3_prefix = s3_url_prefix(bucket, key_prefix)

    def config(self):
        return cf.InitConfig(
            packages=self._packages(),
            files=self._files(),
            commands=self._commands(),
            services=self._services())

    def _packages(self):
        return {
            'apt': {
                'kibana': []
            },
            'python': {
                'boto3': []
            }
        }

    def _files(self):
        return {
            '/opt/kibana/config/kibana_conf.yml': {
                'source': '{}/kibana.yml'.format(self._s3_prefix),
                'mode': '000777',
                'owner': 'kibana',
                'group': 'kibana'
            },
            '/opt/kibana/config/kib_config.py': {
                'source': '{}/kib_config.py'.format(self._s3_prefix),
                'mode': '000777',
                'owner': 'kibana',
                'group': 'kibana'
            }
        }

    def _commands(self):
        return {
            'config_kibana': {
                'command': 'python kib_config.py',
                'cwd': '/opt/kibana/config'
            }
        }

    def _services(self):
        return {
            'sysvinit': {
                'kibana': {
                    'enabled': True,
                    'ensureRunning': True
                }
            }
        }


class FileBeats(object):
    pass
