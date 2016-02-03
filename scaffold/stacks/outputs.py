#!/usr/bin/python

def identity(k):
    return True

def dict(stack_outputs, key_filter = identity):
    return {o['OutputKey'] : o['OutputValue'] for o in stack_outputs if key_filter(o['OutputKey'])}

def keys(stack_outputs, key_filter = identity):
    return [o['OutputKey'] for o in stack_outputs if key_filter(o['OutputKey'])]

def values(stack_outputs, key_filter = identity):
    return [o['OutputValue'] for o in stack_outputs if key_filter(o['OutputKey'])]
