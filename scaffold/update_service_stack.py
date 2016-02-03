
#!/usr/bin/python

import sys
from template.services import ServicesTemplate
import boto3
import stacks

if not len(sys.argv) > 1:
    print 'Usage: update_service_stack (network-stack-name)'
    exit(1)

def output_matching(outputs, key):
    return [o['OutputValue'] for o in outputs if o['OutputKey'] == key][0]

def outputs_containing(outputs, key_fragment):
    return [o['OutputValue'] for o in outputs if key_fragment in o['OutputKey']]

network_stack_name = sys.argv[1]

cf = boto3.resource('cloudformation')
outputs = cf.Stack(network_stack_name).outputs

vpc_id = output_matching(outputs, 'VpcId')
vpc_cidr = output_matching(outputs, 'VpcCidr')
priv_rt_id = output_matching(outputs, 'PrivateRT')
pub_subnet_ids = outputs_containing(outputs, 'PublicSubnet')

template = ServicesTemplate('TestCoreServices',
                            description = 'Core Services',
                            vpc_id = vpc_id,
                            vpc_cidr = vpc_cidr,
                            private_route_table_id = priv_rt_id,
                            public_subnet_ids = pub_subnet_ids)

stack_parms = {
    ServicesTemplate.BASTION_KEY_PARM_NAME : 'bastion'
}

updater = stacks.Updater('CoreServices', template.to_json())
results = updater.update(stack_parms)

print 'ID:     ', results['id']
print 'STATUS: ', results['status']
print 'REASON: ', results['reason']

