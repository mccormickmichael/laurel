import unittest

from ..tiny_userdata import endl


class TestUserdata(unittest.TestCase):

    def test_endl_simple(self):
        lines = ['one', 'two', 'three']
        expected = ['one', '\n', 'two', '\n', 'three', '\n']
        actual = endl(lines)
        self.assertEqual(expected, actual)

    def test_endl_embedded(self):
        lines = ['one', ['sub', 8, 'thing'], 'three']
        expected = ['one', '\n', 'sub', 8, 'thing', '\n', 'three', '\n']
        actual = endl(lines)
        self.assertEqual(expected, actual)
