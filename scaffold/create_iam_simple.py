#!/usr/bin/python

from template.iam_simple import IAM
import stacks

template = IAM('ScaffoldIAM')
parameters = {}

creator = stacks.Creator('scaffold-iam-simple', template.to_json())
results = creator.create(parameters)

print 'ID:     ', results['id']
print 'STATUS: ', results['status']
print 'REASON: ', results['reason']
