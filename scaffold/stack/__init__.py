#!/usr/bin/python

import json

import boto3

from ..doby import Doby


class Parameters(object):

    @staticmethod
    def build(stack_params):
        return Parameters(boto3_stack=None, parms=stack_params).build_stack_parms()

    @staticmethod
    def merge(stack, updated_stack_params):
        return Parameters(stack, updated_stack_params).build_stack_parms()

    def __init__(self, boto3_stack=None, parms={}):
        if boto3_stack is None or boto3_stack.parameters is None:
            stack_parms = []
        else:
            stack_parms = boto3_stack.parameters
        self._parms = {p['ParameterKey']: p['ParameterValue'] for p in stack_parms}
        for k, v in parms.iteritems():
            self._parms[k] = v

    def build_stack_parms(self):
        return [{'ParameterKey': k, 'ParameterValue': v} for k, v in self._parms.items()]

    def to_dict(self):
        return dict(self._parms)

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

    def keys(self, key_filter=lambda x: True):
        return [o['OutputKey'] for o in self._outputs if key_filter(o['OutputKey'])]

    def values(self, key_filter=lambda x: True):
        return [o['OutputValue'] for o in self._outputs if key_filter(o['OutputKey'])]

    def first(self, key_filter):
        return next((o['OutputValue'] for o in self._outputs if key_filter(o['OutputKey'])), None)

    def __len__(self):
        return len(self._outputs)

    def __getitem__(self, key):
        value = self.first(lambda k: k == key)
        if value is None:
            raise KeyError(key)
        return value

    def __iter__(self):
        return (o['OutputKey'] for o in self._outputs)


class Summary(object):
    def __init__(self, boto3_session, stack_name):
        self._session = boto3_session
        self._stack_name = stack_name
        self._load_template()

    def _load_template(self):
        self._template = self._session.client('cloudformation').get_template_summary(StackName=self._stack_name)
        template_d = Doby(self._template)
        self._description = template_d.Description
        self._build_parameters = Doby(json.loads(template_d.Metadata)).BuildParameters

    def description(self):
        return self._description

    def build_parameters(self):
        return self._build_parameters


def outputs(boto3_session, stack_name):
    return Outputs(boto3_session.resource('cloudformation').Stack(stack_name))


def get_template_summary(region, stack_name):
    cf = boto3.client('cloudformation', region_name=region)
    return cf.get_template_summary(StackName=stack_name)


def get_template_metadata(region, stack_name):
    summary = get_template_summary(region, stack_name)
    return json.loads(summary['Metadata'])


def get_stack_description(region, stack_name):
    summary = get_template_summary(region, stack_name)
    return summary['Description']
