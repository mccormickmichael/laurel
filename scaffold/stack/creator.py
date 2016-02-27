#!/usr/bin/python

import boto3

from .operation import StackOperation

class Creator(StackOperation):
    def __init__(self, stack_name, template_body, bucket_name=StackOperation.BUCKET_NAME, region=StackOperation.DEFAULT_REGION):
        super(Creator, self).__init__(stack_name, template_body, bucket_name, region)

    def create(self, stack_params, cb=StackOperation._printing_cb):
        cf = boto3.resource('cloudformation', region_name=self._region)
        
        stack = cf.create_stack(
            StackName = self._stack_name,
            TemplateURL = self._upload_template(),
            Parameters = StackOperation._build_stack_params(stack_params),
            Capabilities = ['CAPABILITY_IAM'],
            TimeoutInMinutes = 10,
            OnFailure = 'ROLLBACK')

        return self._monitor_stack(stack, ['CREATE_IN_PROGRESS'], cb)
