#!/usr/bin/python

from troposphere import Tags

def merge_tags(src, dest):
    """Merge Troposphere Tag objects. Dest values override src values."""
    d = {}
    for st in src.tags + dest.tags:
        d[st['Key']] = st['Value']
    return Tags(**d)

