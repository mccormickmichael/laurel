#!/usr/bin/python

from troposphere import Tags

def normalize_az(region, az):
    if az.startswith(region):
        return az
    return region + az.lower()


def merge_tags(src, dest):
    """Merge Troposphere Tag objects. Dest values override src values."""
    d = {}
    for st in src.tags + dest.tags:
        d[st['Key']] = st['Value']
    return Tags(**d)

