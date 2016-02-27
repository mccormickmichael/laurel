#!/usr/bin/python

import time

import boto3

class StackOperation(object):

    DEFAULT_REGION = 'us-west-2'
    BUCKET_NAME = 'thousandleaves-us-west-2-laurel-deploy'
    KEY_PREFIX = 'scaffold/templates'

    @staticmethod
    def _printing_cb(stack_id, stack_status, status_reason):
        print '{0} - {1} : {2}'.format(stack_id, stack_status, status_reason if status_reason else '')

    @staticmethod
    def _monitor_stack(stack, conditions, callback):
        while stack.stack_status in conditions:
            callback(stack.stack_id, stack.stack_status, stack.stack_status_reason)
            time.sleep(10)
            stack.reload()
        return { 'id' : stack.stack_id,
                 'status' : stack.stack_status,
                 'reason' : stack.stack_status_reason
        }

    @staticmethod
    def _build_stack_params(param_dict):
        return [ { 'ParameterKey' : k, 'ParameterValue' : v } for k, v in param_dict.items() ]

    @staticmethod
    def _to_s3_url(bucket, key):
        return 'http://s3.amazonaws.com/{}/{}'.format(bucket, key)

    def __init__(self, stack_name, template_body, bucket_name, region):
        self._stack_name = stack_name
        self._template_body = template_body
        self._bucket_name = bucket_name
        self._region = region

    def _upload_template(self):
        key_name = '{}/{}'.format(StackOperation.KEY_PREFIX, self._stack_name)
        bucket = boto3.resource('s3', region_name=self._region).Bucket(self._bucket_name)
        bucket.put_object(Key=key_name,
                          Body=self._template_body)
        return StackOperation._to_s3_url(self._bucket_name, key_name)





