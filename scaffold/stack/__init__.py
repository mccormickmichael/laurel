#!/usr/bin/python

from .elements import Outputs, Parameters, Summary


def new_parameters(parms_dict):
    return Parameters(parms=parms_dict)


def parameters(boto3_session, stack_name):
    return Parameters(_get_stack(boto3_session, stack_name))


def outputs(boto3_session, stack_name):
    return Outputs(_get_stack(boto3_session, stack_name))


def summary(boto3_session, stack_name):
    return Summary(boto3_session, stack_name)


def _get_stack(session, name):
    return session.resource('cloudformation').Stack(name)
