#!/usr/bin/python
# Tear down the scaffolding stack

import boto3
import time

cf = boto3.resource('cloudformation')

stack = cf.Stack('scaffold')

stack.delete()

while True:
    print stack.stack_status, stack.stack_status_reason
    time.sleep(10)
    stack.reload()
