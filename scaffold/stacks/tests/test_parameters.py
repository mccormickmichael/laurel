#!/usr/bin/python

import unittest
from .. import Parameters

class TestParameters(unittest.TestCase):

    def setUp(self):
        self.mock_stack = lambda:0
        self.mock_stack.parameters = [
            { 'ParameterKey' : 'StartsWithOne',
              'ParameterValue': 'StartsWithOneValue'},
            { 'ParameterKey' : 'StartsWithTwo',
              'ParameterValue': 'StartsWithTwoValue'},
            { 'ParameterKey' : 'OneWithEnds',
              'ParameterValue': 'OneWithEndsValue'},
            { 'ParameterKey' : 'TwoWithEnds',
              'ParameterValue': 'TwoWithEndsValue'}
        ]

    def test_init_stack(self):
        parms = Parameters(stack=self.mock_stack)
        self.assertEqual(4, len(parms))
        
    def test_init_parms(self):
        parms = Parameters(parms={'One': 'Value', 'Two': 'Thing'})
        self.assertEqual(2, len(parms))

    def test_getitem(self):
        parms = Parameters(stack=self.mock_stack)
        self.assertEqual('StartsWithOneValue', parms['StartsWithOne'])

    def test_getitem_nokey(self):
        parms = Parameters(stack=self.mock_stack)
        with self.assertRaises(KeyError):
            parms['Blah']

    def test_setitem(self):
        parms = Parameters(stack=self.mock_stack)
        parms['Thing'] = 'Biggles'
        self.assertEqual('Biggles', parms['Thing'])

    def test_setitem_exists(self):
        parms = Parameters(stack=self.mock_stack)
        parms['StartsWithOne'] = 'Biggles'
        self.assertEqual('Biggles', parms['StartsWithOne'])

    def test_delitem(self):
        parms = Parameters(stack=self.mock_stack)
        del parms['StartsWithOne']
        self.assertFalse('StartsWithOne' in parms)
