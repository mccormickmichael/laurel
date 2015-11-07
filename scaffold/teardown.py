#!/usr/bin/python
# Tear down the scaffolding stack

import boto3
import time

cf = boto3.resource('cloudformation')

stack = cf.Stack('Scaffold')

stack.delete()

while stack.stack_status == 'DELETE_IN_PROGRESS':
    print stack.stack_status, stack.stack_status_reason
    time.sleep(10)
    stack.reload()
    
print stack.stack_status, stack.stack_status_reason
