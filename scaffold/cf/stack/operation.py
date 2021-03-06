#!/usr/bin/python

import logging
import time

import botocore

from . import Parameters
from . import _get_stack

logger = logging.getLogger('laurel.cf.operation')


def _logging_cb(stack_id, stack_status, status_reason):
    logger.info('%s - %s : %s', stack_id, stack_status, status_reason)

def _printing_cb(stack_id, stack_status, status_reason):
    print '{0} - {1} : {2}'.format(stack_id, stack_status, status_reason if status_reason else '')


# TODO: _monitor_stack could use the cloudformation client and query by stack ID
#       This would prevent boto3 from throwing an exception in the case of stack deletion
def _monitor_stack(stack, conditions, callback):
    while stack.stack_status in conditions:
        callback(stack.stack_id, stack.stack_status, stack.stack_status_reason)
        time.sleep(10)
        stack.reload()


def _to_s3_url(bucket, key):
    return 'http://s3.amazonaws.com/{}/{}'.format(bucket, key)


class StackOperation(object):
    def __init__(self, boto3_session, stack_name, template_body, capabilities, bucket_name, key_prefix):
        self._stack_name = stack_name
        self._session = boto3_session
        self._capabilities = capabilities
        self._bucket_name = bucket_name
        self._key_prefix = key_prefix
        self._template_url = self._upload_template(template_body)

    def create(self, stack_params={}, progress_callback=_logging_cb):
        cf = self._session.resource('cloudformation')

        parameters = Parameters(parms=stack_params)

        stack = cf.create_stack(
            StackName=self._stack_name,
            TemplateURL=self._template_url,
            Parameters=parameters.to_stack_parms(),
            Capabilities=self._capabilities,
            TimeoutInMinutes=10,
            OnFailure='ROLLBACK')
        # TODO: Add notificationArn and Stack Tags

        _monitor_stack(stack, ['CREATE_IN_PROGRESS', 'ROLLBACK_IN_PROGRESS'], progress_callback)
        return stack

    def update(self, updated_stack_params={}, progress_callback=_logging_cb):
        cf = self._session.resource('cloudformation')

        stack = cf.Stack(self._stack_name)
        parameters = Parameters(boto3_stack=stack)
        parameters.update(updated_stack_params)
        stack.update(TemplateURL=self._template_url,
                     Parameters=parameters.to_stack_parms(),
                     Capabilities=self._capabilities)
        # TODO: Add notificationArn and Stack Tags

        _monitor_stack(stack, ['UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
                               'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
                               'UPDATE_ROLLBACK_IN_PROGRESS'], progress_callback)
        return stack

    def _upload_template(self, template_body):
        key_name = '{}/{}.template'.format(self._key_prefix, self._stack_name)
        bucket = self._session.resource('s3').Bucket(self._bucket_name)
        bucket.put_object(Key=key_name,
                          Body=template_body)
        return _to_s3_url(self._bucket_name, key_name)


class StackDeleter(object):
    def __init__(self, boto3_session, stack_name):
        self._session = boto3_session
        self._stack_name = stack_name

    def validate_stack_exists(self):
        _get_stack(self._session, self._stack_name).load()  # this will throw if the stack does not exist.
        return True

    def delete(self, progress_callback=_logging_cb):
        stack = _get_stack(self._session, self._stack_name)
        stack.delete()
        try:
            _monitor_stack(stack, ['DELETE_IN_PROGRESS'], progress_callback)
        except botocore.exceptions.ClientError:
            # this is okay, we expect to get this exception when the stack is deleted.
            pass
