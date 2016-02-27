#!/usr/bin/python

import boto3

from .operation import StackOperation
from . import Parameters

class Updater(StackOperation):

    def __init__(self, stack_name, template_body=None, bucket_name=StackOperation.BUCKET_NAME, region=StackOperation.DEFAULT_REGION):
        super(Updater, self).__init__(stack_name, template_body, bucket_name, region)

    def update(self, stack_params, cb=StackOperation._printing_cb):
        cf = boto3.resource('cloudformation', region_name=self._region)
        stack = cf.Stack(self._stack_name)
        parameters = Parameters(stack=stack, parms=stack_parms)
        if self._template_body is None:
            stack.update(UsePreviousTemplate=True,
                         Parameters=parameters.for_stack(),
                         Capabilities=['CAPABILITY_IAM'])
        else:
            stack.update(TemplateURL=self._upload_template(),
                         Parameters=parameters.for_stack(),
                         Capabilities=['CAPABILITY_IAM'])

        return StackOperation._monitor_stack(stack, ['UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS'], cb)

