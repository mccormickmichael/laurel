#!/usr/bin/python

import time
import json
import boto3
import template


DEFAULT_REGION = 'us-west-2'
BUCKET_NAME = 'thousandleaves-us-west-2-laurel-deploy'
KEY_PREFIX = 'scaffold/templates'


def printing_cb(stack_id, stack_status, status_reason):
    print '{0} - {1} : {2}'.format(stack_id, stack_status, status_reason if status_reason else '')

    
def _parse_stack_params(stack_params):
    if stack_params is None:
        return {}
    return {p['ParameterKey'] : p['ParameterValue'] for p in stack_params}


def _build_stack_params(param_dict):
    return [ { 'ParameterKey' : k, 'ParameterValue' : v } for k, v in param_dict.items() ]


def _merge_stack_params(stack, update_params):
    current_params = _parse_stack_params(stack.parameters)
    for k, v in update_params.items():
        current_params[k] = v
    return _build_stack_params(current_params)


def _monitor_stack(stack, conditions, callback):
    while stack.stack_status in conditions:
        callback(stack.stack_id, stack.stack_status, stack.stack_status_reason)
        time.sleep(10)
        stack.reload()
    return { 'id' : stack.stack_id,
             'status' : stack.stack_status,
             'reason' : stack.stack_status_reason
    }


def _to_s3_url(bucket, key):
    return 'http://s3.amazonaws.com/{}/{}'.format(bucket, key)


def get_template_summary(region, stack_name):
    cf = boto3.client('cloudformation', region_name=region)
    return cf.get_template_summary(StackName=stack_name)


def get_template_metadata(region, stack_name):
    summary = get_template_summary(region, stack_name)
    return json.loads(summary['Metadata'])


def get_template_build_parms(region, stack_name):
    return get_template_metadata(region, stack_name)[template.BUILD_PARMS_NAME]


def get_stack_description(region, stack_name):
    summary = get_template_summary(region, stack_name)
    return summary['Description']


class StackOperation(object):
    def __init__(self, stack_name, template_body, bucket_name, region):
        self.stack_name = stack_name
        self.template_body = template_body
        self.bucket_name = bucket_name
        self.region = region

    def _upload_template(self):
        key_name = '{}/{}'.format(KEY_PREFIX, self.stack_name)
        bucket = boto3.resource('s3', region_name = self.region).Bucket(self.bucket_name)
        bucket.put_object(Key = key_name,
                          Body = self.template_body)
        return _to_s3_url(self.bucket_name, key_name)

    
class Creator(StackOperation):
    def __init__(self, stack_name, template_body, bucket_name = BUCKET_NAME, region = DEFAULT_REGION):
        super(Creator, self).__init__(stack_name, template_body, bucket_name, region)

    def create(self, stack_params, cb = printing_cb):
        cf = boto3.resource('cloudformation', region_name = self.region)
        
        stack = cf.create_stack(
            StackName = self.stack_name,
            TemplateURL = self._upload_template(),
            Parameters = _build_stack_params(stack_params),
            Capabilities = ['CAPABILITY_IAM'],
            TimeoutInMinutes = 10,
            OnFailure = 'ROLLBACK')

        return _monitor_stack(stack, ['CREATE_IN_PROGRESS'], cb)


class Updater(StackOperation):
    def __init__(self, stack_name, template_body = None, bucket_name = BUCKET_NAME, region = DEFAULT_REGION):
        super(Updater, self).__init__(stack_name, template_body, bucket_name, region)

        
    def update(self, stack_params, cb = printing_cb):
        cf = boto3.resource('cloudformation', region_name = self.region)
        stack = cf.Stack(self.stack_name)
        parameters = _merge_stack_params(stack, stack_params)
        if self.template_body is None:
            stack.update(UsePreviousTemplate = True,
                         Parameters = parameters,
                         Capabilities = ['CAPABILITY_IAM'])
        else:
            stack.update(TemplateURL = self._upload_template(),
                         Parameters = parameters,
                         Capabilities = ['CAPABILITY_IAM'])

        return _monitor_stack(stack, ['UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS'], cb)
