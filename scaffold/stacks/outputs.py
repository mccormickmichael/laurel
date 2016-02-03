#!/usr/bin/python

import types

def _identity(k):
    return True

_function_types = [types.FunctionType, types.LambdaType]

def dict(stack_outputs, key_filter = _identity):
    return {o['OutputKey'] : o['OutputValue'] for o in stack_outputs if key_filter(o['OutputKey'])}

def keys(stack_outputs, key_filter = _identity):
    return [o['OutputKey'] for o in stack_outputs if key_filter(o['OutputKey'])]

def values(stack_outputs, key_filter = _identity):
    return [o['OutputValue'] for o in stack_outputs if key_filter(o['OutputKey'])]

def value(stack_outputs, key):
    if type(key) in _function_types:
        return next( (o['OutputValue'] for o in stack_outputs if key(o['OutputKey'])), None )
    return value(stack_outputs, lambda k: k == key)
