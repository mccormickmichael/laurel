#!/usr/bin/python

# update the scaffolding stack

import boto3
import stack
import time

cf = boto3.resource('cloudformation')

template = stack.create_template()

stack = sf.Stack('Scaffold')

stack.update(
    TemplateBody = template,
    Parameters = [],
    Capabilities = ['CAPABILITY_IAM'],
    TimeoutMinutes = 10,
    OnFailure = 'ROLLBACK')

while stack_status == 'UPDATE_IN_PROGRESS':
    print stack.stack_status, stack.stack_status_reason
    time.sleep(10)
    stack.reload()

print stack.stack_status, stack.stack_status_reason
