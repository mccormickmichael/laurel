#!/usr/bin/python

import troposphere as tp
import troposphere.autoscaling as autoscaling

def tags_to_dict(taglist):
    return { t['Key'] : t['Value'] for t in taglist }

def retag(default_tags, **kwargs):
    """Add/replace tag objects; kwargs overrides existing tag values"""
    d = tags_to_dict(default_tags.tags)
    d.update(**kwargs)
    return tp.Tags(**d)

def asgtag(tags):
    """Turn regular cloudformation Tags into autoscaling Tags"""
    d = tags_to_dict(tags.tags)
    return autoscaling.Tags(**d)

def mergetag(a, b):
    """Merge Troposphere Tag objects. Dest values override src values."""
    d = tags_to_dict(a.tags + b.tags)
    return tp.Tags(**d)

