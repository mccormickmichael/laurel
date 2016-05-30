#!/usr/bin/python

import unittest

from troposphere import Tags

from .. import retag, asgtag, mergetag


class test_tags(unittest.TestCase):
    def test_merge_tags(self):
        src = Tags(Application='ApplicationTag', Name='NameTag', Zip='Blah')
        dest = Tags(Name='ReplacementTag')
        result = mergetag(src, dest)
        self.assertEqual(3, len(result.tags))
        self.assertEqual('ReplacementTag', [t['Value'] for t in result.tags if t['Key'] == 'Name'][0])
        self.assertEqual('Blah', [t['Value'] for t in result.tags if t['Key'] == 'Zip'][0])

    def test_asg_tag(self):
        src = Tags(Application='ApplicationTag', Name='NameTag', Zip='Blah')
        result = asgtag(src)
        for t in result.tags:
            self.assertIsNotNone(t['PropagateAtLaunch'], msg=t['Key'])

    def test_retag(self):
        src = Tags(Application='ApplicationTag', Name='NameTag', Zip='Blah')
        result = retag(src, Name='NewName', Thing='Thing')
        self.assertEqual('NewName', [t['Value'] for t in result.tags if t['Key'] == 'Name'][0])
        self.assertEqual('Thing', [t['Value'] for t in result.tags if t['Key'] == 'Thing'][0])
