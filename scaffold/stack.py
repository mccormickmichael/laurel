#!/usr/bin/python

import sys
import time
import boto3

def print_cb(stack_id, stack_status, status_reason):
    print '{0} - {1} : {2}'.format(stack_id, stack_status, status_reason if status_reason else '')

def create(stack_name, stack_params, template_body, cb = print_cb):
    cf = boto3.resource('cloudformation')
    
    stack = cf.create_stack(
        StackName = stack_name,
        TemplateBody = template_body,
        Parameters = build_stack_params(stack_params),
        Capabilities = ['CAPABILITY_IAM'],
        TimeoutInMinutes = 10,
        OnFailure = 'ROLLBACK')

    while stack.stack_status  == 'CREATE_IN_PROGRESS':
        cb(stack.stack_id, stack.stack_status, stack.stack_status_reason)
        time.sleep(10)
        stack.reload()

    return { 'id' : stack.stack_id,
             'status' : stack.stack_status,
             'reason' : stack.stack_status_reason
             }

def build_stack_params(param_dict):
    params = []
    for k, v in param_dict.items():
        params.append({
            'ParameterKey'   : k,
            'ParameterValue' : v
            })
    return params
