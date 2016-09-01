import unittest

from scaffold.vpc.vpc_template import VpcTemplate


class TestVpcNxN(unittest.TestCase):

    def test_instantiate(self):
        # should pass without throwing any exceptions
        VpcTemplate('TestTemplate')
