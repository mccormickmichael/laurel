#!/usr/bin/python

import unittest
from .. import Parameters


class TestParameters(unittest.TestCase):

    def setUp(self):
        def mock_stack(): 0
        mock_stack.parameters = [
            {'ParameterKey': 'StartsWithOne',
             'ParameterValue': 'StartsWithOneValue'},
            {'ParameterKey': 'StartsWithTwo',
             'ParameterValue': 'StartsWithTwoValue'},
            {'ParameterKey': 'OneWithEnds',
             'ParameterValue': 'OneWithEndsValue'},
            {'ParameterKey': 'TwoWithEnds',
             'ParameterValue': 'TwoWithEndsValue'}
        ]
        self.mock_stack = mock_stack

    def test_init_stack(self):
        parms = Parameters(boto3_stack=self.mock_stack)
        self.assertEqual(4, len(parms))

    def test_init_parms(self):
        parms = Parameters(parms={'One': 'Value', 'Two': 'Thing'})
        self.assertEqual(2, len(parms))

    def test_getitem(self):
        parms = Parameters(boto3_stack=self.mock_stack)
        self.assertEqual('StartsWithOneValue', parms['StartsWithOne'])

    def test_getitem_nokey(self):
        parms = Parameters(boto3_stack=self.mock_stack)
        with self.assertRaises(KeyError):
            parms['Blah']

    def test_setitem(self):
        parms = Parameters(boto3_stack=self.mock_stack)
        parms['Thing'] = 'Biggles'
        self.assertEqual('Biggles', parms['Thing'])

    def test_setitem_exists(self):
        parms = Parameters(boto3_stack=self.mock_stack)
        parms['StartsWithOne'] = 'Biggles'
        self.assertEqual('Biggles', parms['StartsWithOne'])

    def test_delitem(self):
        parms = Parameters(boto3_stack=self.mock_stack)
        del parms['StartsWithOne']
        self.assertFalse('StartsWithOne' in parms)

    def test_merge(self):
        new_parms = {'StartsWithOne': 'biggles'}
        parms = Parameters(boto3_stack=self.mock_stack, parms=new_parms)
        self.assertEqual('biggles', parms['StartsWithOne'])

    def test_update(self):
        new_parms = {'StartsWithOne': 'biggles'}
        parameters = Parameters(boto3_stack=self.mock_stack)
        parameters.update(new_parms)
        self.assertEqual('biggles', parameters['StartsWithOne'])
