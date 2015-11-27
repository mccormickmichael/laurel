from iam_simple import IAM
import stack

template = IAM('ScaffoldIAM')
parameters = {
    'BOGUS': 'FakeParameterValue'
}

updater = stack.Updater('scaffold-iam-simple', template.to_json())
results = updater.update({})

print 'ID:     ', results['id']
print 'STATUS: ', results['status']
print 'REASON: ', results['reason']
