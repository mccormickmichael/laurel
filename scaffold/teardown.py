#!/usr/bin/python
# Tear down the scaffolding stack

import sys
import time
import boto3
import botocore

cf = boto3.resource('cloudformation')

stack_name = sys.argv[1]
stack = cf.Stack(stack_name)

stack.delete()

while stack.stack_status == 'DELETE_IN_PROGRESS':
    print stack.stack_status, stack.stack_status_reason
    time.sleep(10)
    try:
        stack.reload()
    except botocore.exceptions.ClientError:
        # okay, we expect to get this when the stack is deleted.
        pass
    
print 'stack {} deleted'.format(stack_name)
