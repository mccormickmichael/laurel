#!/usr/bin/python

import sys
from template.vpc_nxn import NxNVPC
import stack

if not len(sys.argv) > 1:
    print 'Usage: python create_vpc_nxn.py (desired-stack-name)'
    exit(1)

stack_name = sys.argv[1]

# TODO: more stack template parameters?
# TODO: I can see why you might want to combine stack create/update,
#       because they both require the same parameters for the template,
#       and probably similar parameters for the stack itself.
    
template = NxNVPC(stack_name, description = 'Network stack for infrastructure services')
creator = stack.Creator('{}VPC'.format(stack_name), template.to_json())
results = creator.create({})

print 'ID:     ', results['id']
print 'STATUS: ', results['status']
print 'REASON: ', results['reason']
