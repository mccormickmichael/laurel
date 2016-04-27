#!/usr/bin/python

import unittest

from .. import doby


class TestDoby(unittest.TestCase):

    def test_attr(self):
        expected_value = 'value'
        d = doby.Doby(dict(Attr=expected_value))
        self.assertEqual(expected_value, d.Attr)

    def test_missing_attr(self):
        d = doby.Doby()
        with self.assertRaises(KeyError):
            d.Thing

    def test_nested_dict(self):
        d = doby.Doby({'outer': {'inner': 'value'}})
        self.assertEqual('value', d.outer.inner)

    def test_nested_list(self):
        d = doby.Doby({'outer': [{'inner': 'value'}, 'two']})
        self.assertEqual('value', d.outer[0].inner)

    def test_nested_tuple(self):
        d = doby.Doby({'outer': ({'inner': 'value'}, 'two')})
        self.assertEqual('value', d.outer[0].inner)

    def test_dict_syntax(self):
        d = doby.Doby({'outer': {'inner': 'value'}})
        self.assertEqual('value', d['outer'].inner)
