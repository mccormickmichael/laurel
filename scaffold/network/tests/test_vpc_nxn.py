import unittest

from scaffold.network.vpc_template import VpcTemplate


class TestVpcNxN(unittest.TestCase):

    def test_instantiate(self):
        # should pass without throwing any exceptions
        VpcTemplate('TestTemplate')
