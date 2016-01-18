#!/usr/bin/python

from template.vpc_nxn import NxNVPC
import stack

template = NxNVPC('Test')
creator = stack.Creator('TestNxNVPC', template.to_json())
results = creator.create({})

print 'ID:     ', results['id']
print 'STATUS: ', results['status']
print 'REASON: ', results['reason']
