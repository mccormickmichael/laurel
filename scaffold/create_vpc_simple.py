#!/usr/bin/python

from vpc_simple import SimpleVPC
import stack

template = SimpleVPC('Scaffold')
parameters = {
    template.PARM_KEY_NAME: 'bastion'
    }
creator = stack.Creator('scaffold-vpc-simple', template.to_json())
results = creator.create(parameters)

print 'ID:     ', results['id']
print 'STATUS: ', results['status']
print 'REASON: ', results['reason']
