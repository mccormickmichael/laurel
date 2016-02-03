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

    def test_keys_mapping(self):
        results = outputs.keys(self.stack_outputs, lambda k: k.startswith('Starts'))
        self.assertEqual(['StartsWithOne', 'StartsWithTwo'], results)

    def test_keys_mapping_default(self):
        results = outputs.keys(self.stack_outputs)
        self.assertEqual(4, len(results))

    def test_values_mapping(self):
        results = outputs.values(self.stack_outputs, lambda v: v.endswith('Ends'))
        self.assertEqual(['OneWithEndsValue', 'TwoWithEndsValue'], results)

    def test_values_mapping_default(self):
        results = outputs.values(self.stack_outputs)
        self.assertEqual(4, len(results))

    def test_value(self):
        result = outputs.value(self.stack_outputs, 'TwoWithEnds')
        self.assertEquals('TwoWithEndsValue', result)

    def test_value_lambda(self):
        result = outputs.value(self.stack_outputs, lambda k: k.startswith('Starts'))
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith('Starts') and result.endswith('Value'))

    def test_value_none(self):
        self.assertIsNone(outputs.value(self.stack_outputs, 'Biggles'))
