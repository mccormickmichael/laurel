#!/usr/bin/python

import time
import json

import boto3

from .template import BUILD_PARMS_NAME


DEFAULT_REGION = 'us-west-2'
BUCKET_NAME = 'thousandleaves-us-west-2-laurel-deploy'
KEY_PREFIX = 'scaffold/templates'

def _identity(k):
    return True

def _parse_stack_parms(stack_parms):
    return {p['ParameterKey'] : p['ParameterValue'] for p in stack_parms}

class Parameters(object):

    def __init__(self, stack=None, parms={}):
        stack_parms = [] if stack is None else stack.parameters
        self._parms = _parse_stack_parms(stack_parms)
        for k, v in parms.iteritems():
            self._parms[k] = v

    def for_stack(self):
        """Produce a list of parameters suitable for use in stack operations"""
        return [{'ParameterKey': k, 'ParameterValue':v} for k, v in self._parms.iteritems()]

    def __len__(self):
        return len(self._parms)

    def __getitem__(self, key):
        return self._parms[key]

    def __setitem__(self, key, value):
        self._parms[key] = value

    def __delitem__(self, key):
        del self._parms[key]

    def __iter__(self):
        return iter(self._parms)

class Outputs(object):
    def __init__(self, boto3_stack):
        self._outputs = boto3_stack.outputs

    def keys(self, key_filter=_identity):
        return [o['OutputKey'] for o in self._outputs if key_filter(o['OutputKey'])]

    def values(self, key_filter=_identity):
        return [o['OutputValue'] for o in self._outputs if key_filter(o['OutputKey'])]

    def first(self, key_filter):
        return next( (o['OutputValue'] for o in self._outputs if key_filter(o['OutputKey'])), None)

    def __len__(self):
        return len(self._outputs)

    def __getitem__(self, key):
        value = self.first(lambda k: k == key)
        if value is None:
            raise KeyError(key)
        return value

    def __iter__(self):
        return (o['OutputKey'] for o in self._outputs)


def get_template_summary(region, stack_name):
    cf = boto3.client('cloudformation', region_name=region)
    return cf.get_template_summary(StackName=stack_name)


def get_template_metadata(region, stack_name):
    summary = get_template_summary(region, stack_name)
    return json.loads(summary['Metadata'])


def get_template_build_parms(region, stack_name):
    return get_template_metadata(region, stack_name)[BUILD_PARMS_NAME]


def get_stack_description(region, stack_name):
    summary = get_template_summary(region, stack_name)
    return summary['Description']


