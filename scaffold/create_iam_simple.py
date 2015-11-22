from iam_simple import IAM
import stack

template = IAM('ScaffoldIAM')
parameters = {}

results = stack.create('Scaffold-IAM', parameters, template.to_json())

print 'ID:     ', results['id']
print 'STATUS: ', results['status']
print 'REASON: ', results['reason']
