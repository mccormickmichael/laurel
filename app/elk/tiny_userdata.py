

def endl(lines):
    '''Insert a "\n" between items in a list in preparation for wrapping in a Fn::Join.
    Items that are themselves arrays are flattened and a single "\n" is added
    '''
    result = []
    for line in lines:
        if type(line) in (list, tuple):
            result.extend(line)
        else:
            result.append(line)
        result.append('\n')
    return result


def userdata_prelude():
    return [
        '#!/bin/bash',
        'yum -y update && yum -y install yum-cron && chkconfig yum-cron on'
    ]


def eni_attach(eni_ref, region):
    return [
        ['ENI_ID=', eni_ref],
        'INS_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)',
        ['aws ec2 attach-network-interface --instance-id $INS_ID --device-index 1 --network-interface-id $ENI_ID --region ', region],
        'echo $ENI_ID > /tmp/eni_id'
    ]

def write_es_host(es_host_ref):
    return [
        ['echo ', es_host_ref, ' > /tmp/es_host']
    ]


def cfn_init(stack_ref, resource_name, configsets, region):
    return [
        ['/opt/aws/bin/cfn-init -v --stack ', stack_ref,
         ' --resource ', resource_name,
         ' --configsets ', ','.join(configsets),
         ' --region ', region]
    ]


class ESUserdata(object):

    def __init__(self, stack_ref, resource_name, configsets, region):
        self._userdata = userdata_prelude() \
                         + cfn_init(stack_ref, resource_name, configsets, region)

    def items(self):
        return endl(self._userdata)


class LogstashUserdata(object):

    def __init__(self, eni_id, es_host_ref, stack_ref, resource_name, configsets, region):
        self._userdata = userdata_prelude() \
                         + eni_attach(eni_id, region) \
                         + write_es_host(es_host_ref) \
                         + cfn_init(stack_ref, resource_name, configsets, region)

    def items(self):
        return endl(self._userdata)
