#!/usr/bin/python

from template.vpc_nxn import NxNVPC
import stack

template = NxNVPC('Test')
creator = stack.Updater('TestNxNVPC', template.to_json())
results = creator.update({})

print 'ID:     ', results['id']
print 'STATUS: ', results['status']
print 'REASON: ', results['reason']
