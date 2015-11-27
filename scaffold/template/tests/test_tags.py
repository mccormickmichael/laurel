#!/usr/bin/python

import unittest
from troposphere import Tags
from .. import utils

class test_tags(unittest.TestCase):
    def test_merge_tags(self):
        src = Tags(Application = 'ApplicationTag', Name = 'NameTag', Zip = 'Blah')
        dest = Tags(Name = 'ReplacementTag')
        result = utils.merge_tags(src, dest)
        self.assertEqual(3, len(result.tags))
        self.assertEqual('ReplacementTag', [t['Value'] for t in result.tags if t['Key'] == 'Name'][0])
        self.assertEqual('Blah', [t['Value'] for t in result.tags if t['Key'] == 'Zip'][0])
