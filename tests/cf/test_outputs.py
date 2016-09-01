#!/usr/bin/python

import unittest

from scaffold.cf.stack.elements import Outputs


class TestOutputs(unittest.TestCase):

    def setUp(self):
        def mock_stack(): 0
        mock_stack.outputs = [
            {'OutputKey': 'StartsWithOne',
             'OutputValue': 'StartsWithOneValue'},
            {'OutputKey': 'StartsWithTwo',
             'OutputValue': 'StartsWithTwoValue'},
            {'OutputKey': 'OneWithEnds',
             'OutputValue': 'OneWithEndsValue'},
            {'OutputKey': 'TwoWithEnds',
             'OutputValue': 'TwoWithEndsValue'}
        ]
        self.outputs = Outputs(mock_stack)

    def test_len(self):
        self.assertEqual(4, len(self.outputs))

    def test_getitem(self):
        self.assertEquals('StartsWithOneValue', self.outputs['StartsWithOne'])

    def test_getitem_nokey(self):
        with self.assertRaises(KeyError):
            self.outputs['Blah']

    def test_key_filter(self):
        results = self.outputs.keys(lambda k: k.startswith('Starts'))
        self.assertEqual(['StartsWithOne', 'StartsWithTwo'], results)

    def test_all_keys(self):
        results = self.outputs.keys()
        self.assertEqual(4, len(results))

    def test_value_filter(self):
        results = self.outputs.values(lambda v: v.endswith('Ends'))
        self.assertEqual(['OneWithEndsValue', 'TwoWithEndsValue'], results)

    def test_all_values(self):
        results = self.outputs.values()
        self.assertEqual(4, len(results))

    def test_first(self):
        result = self.outputs.first(lambda k: k.endswith('Ends'))
        self.assertEqual('OneWithEndsValue', result)

    def test_iter(self):
        count = 0
        for k in self.outputs:
            self.assertTrue('With' in k)
            self.assertFalse('Value' in k)
            count += 1
        self.assertEqual(4, count)
