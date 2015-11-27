#!/usr/bin/python

from template.vpc_simple import SimpleVPC
import stack

template = SimpleVPC('Scaffold')
parameters = {
    template.PARM_KEY_NAME: 'bastion'
}

updater = stack.Updater('scaffold-vpc-simple', template.to_json())
results = updater.update(parameters)

print 'ID:     ', results['id']
print 'STATUS: ', results['status']
print 'REASON: ', results['reason']
