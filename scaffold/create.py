#!/usr/bin/python

# stand up the scaffolding stack

import time
import boto3
import template

cf = boto3.resource('cloudformation')

template_body = template.create_template()

stack = cf.create_stack(
    StackName = 'Scaffold',
    TemplateBody = template_body,
    Parameters = [], #TODO will probably have some parameters, yes?
    Capabilities = ['CAPABILITY_IAM'],
    TimeoutInMinutes = 10,
    OnFailure = 'ROLLBACK')

print stack.stack_id

while stack.stack_status == 'CREATE_IN_PROGRESS':
    print stack.stack_status, stack.stack_status_reason
    time.sleep(10)
    stack.reload()

print stack.stack_status, stack.stack_status_reason
