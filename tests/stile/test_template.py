import unittest

from scaffold.stile.stile_template import StileTemplate


class TestStileTemplate(unittest.TestCase):

    def test_instantiate(self):
        # should pass without throwing any exceptions
        StileTemplate('TestTemplate', 'vpc-deadbeef', '10.0.0.0/8', 'rtb-deadbeef', ['subnet-cab4abba'])
