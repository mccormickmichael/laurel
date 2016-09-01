import unittest

from scaffold.consul.consul_template import ConsulTemplate


class TestConsulTemplate(unittest.TestCase):

    def test_instantiate(self):
        # should pass without throwing any exceptions
        ConsulTemplate('TestTemplate', 'us-west-2', 'bucket', 'prefix', 'vpc-deadbeef', '10.0.0.0/8', ['subnet-cab4abba'], [])
