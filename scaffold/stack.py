#!/usr/bin/python

import sys
import time
import boto3


bucket_name = 'thousandleaves-us-west-2-laurel-deploy'
key_prefix = 'scaffold/templates'

def printing_cb(stack_id, stack_status, status_reason):
    print '{0} - {1} : {2}'.format(stack_id, stack_status, status_reason if status_reason else '')

def to_s3_url(bucket, key):
    return 'http://s3.amazonaws.com/{}/{}'.format(bucket, key)

def upload_template(stack_name, template_body):
    key_name = '{}/{}'.format(key_prefix, stack_name)
    bucket = boto3.resource('s3').Bucket(bucket_name)
    bucket.put_object(Key = key_name,
                      Body = template_body)
    return to_s3_url(bucket_name, key_name)
    

def create(stack_name, stack_params, template_body, cb = printing_cb):
    cf = boto3.resource('cloudformation')

    template_url = upload_template(stack_name, template_body)
    print template_url

    stack = cf.create_stack(
        StackName = stack_name,
        TemplateURL = template_url,
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
