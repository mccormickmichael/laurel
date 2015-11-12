#!/usr/bin/python

# update the scaffolding stack

import time
import boto3
import template

cf = boto3.resource('cloudformation')

template_body = template.create_template()

stack = cf.Stack('Scaffold')

stack.update(
    TemplateBody = template_body,
    Parameters = [],
    Capabilities = ['CAPABILITY_IAM'])

while stack.stack_status == 'UPDATE_IN_PROGRESS':
    print stack.stack_status, stack.stack_status_reason
    time.sleep(10)
    stack.reload()

print stack.stack_status, stack.stack_status_reason
