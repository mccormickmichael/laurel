#!/usr/bin/python

from vpc_simple import SimpleVPC
import stack

template = SimpleVPC('Scaffold')
parameters = {
    template.PARM_KEY_NAME: 'bastion'
    }

results = stack.create('scaffold-vpc-simple', parameters, template.to_json())

print 'ID:     ', results['id']
print 'STATUS: ', results['status']
print 'REASON: ', results['reason']
