#!/usr/bin/python

from template.iam_simple import IAM
import stacks

template = IAM('ScaffoldIAM')
parameters = {
    'BOGUS': 'FakeParameterValue'
}

updater = stacks.Updater('scaffold-iam-simple', template.to_json())
results = updater.update({})

print 'ID:     ', results['id']
print 'STATUS: ', results['status']
print 'REASON: ', results['reason']
