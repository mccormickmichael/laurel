#!/usr/bin/python

import sys
from template.vpc_nxn import NxNVPC
import stacks

# TODO: replace with argparse

if not len(sys.argv) > 1:
    print 'Usage: python update_vpc_nxn.py (desired-stack-name)'
    exit(1)

stack_name = sys.argv[1]

# TODO: query existing stack for relevant template and stack parameters
    
template = NxNVPC(stack_name, description = 'Network stack for infrastructure services')
creator = stacks.Updater('{}VPC'.format(stack_name), template.to_json())
results = creator.update({})

print 'ID:     ', results['id']
print 'STATUS: ', results['status']
print 'REASON: ', results['reason']
