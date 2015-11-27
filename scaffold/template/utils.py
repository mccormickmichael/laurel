#!/usr/bin/python

def merge_tags(src, dest):
    """Merge Troposphere Tag objects, replacing any key value in src with matching key values in dest. Dest is modified"""
    for st in src.tags:
        match = False
        for dt in dest.tags:
            if st['Key'] == dt['Key']:
                match = True
                break
        if not match:
            dest.tags.append(st)
    return dest
