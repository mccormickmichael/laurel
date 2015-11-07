#!/usr/bin/python

# stand up the scaffolding stack

import boto3
import stack
import time

cf = boto3.resource('cloudformation')

template = stack.create_template()

stack = cf.create_stack(
    StackName = 'Scaffold',
    TemplateBody = template,
    Parameters = [], #TODO will probably have some parameters, yes?
    Capabilities = ['CAPABILITY_IAM'],
    TimeoutInMinutes = 10,
    OnFailure = 'ROLLBACK')

print stack.stack_id

while True:
    print stack_status, stack_status_reason
    time.sleep(10)
    stack.reload()
