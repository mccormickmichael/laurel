#!/usr/bin/python

import unittest
from .. import outputs

class TestOutputMappings(unittest.TestCase):

    def setUp(self):
        self.stack_outputs = [
            { 'OutputKey' : 'StartsWithOne',
              'OutputValue': 'StartsWithOneValue'},
            { 'OutputKey' : 'StartsWithTwo',
              'OutputValue': 'StartsWithTwoValue'},
            { 'OutputKey' : 'OneWithEnds',
              'OutputValue': 'OneWithEndsValue'},
            { 'OutputKey' : 'TwoWithEnds',
              'OutputValue': 'TwoWithEndsValue'}
        ]

    def test_dict_mapping(self):
        results = outputs.dict(self.stack_outputs, lambda k: k.endswith('Ends'))
        self.assertEqual(2, len(results.keys()))
        self.assertEqual(['OneWithEnds', 'TwoWithEnds'], results.keys())

    def test_dict_mapping_default(self):
        results = outputs.dict(self.stack_outputs)
        self.assertEqual(4, len(results.keys()))

    def test_key_mapping(self):
        results = outputs.keys(self.stack_outputs, lambda k: k.startswith('Starts'))
        self.assertEqual(['StartsWithOne', 'StartsWithTwo'], results)

    def test_key_mapping_default(self):
        results = outputs.keys(self.stack_outputs)
        self.assertEqual(4, len(results))

    def test_value_mapping(self):
        results = outputs.values(self.stack_outputs, lambda v: v.endswith('Ends'))
        self.assertEqual(['OneWithEndsValue', 'TwoWithEndsValue'], results)

    def test_value_mapping_default(self):
        results = outputs.values(self.stack_outputs)
        self.assertEqual(4, len(results))
