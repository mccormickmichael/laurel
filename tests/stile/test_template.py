import unittest

from scaffold.services.services_template import ServicesTemplate


class TestServicesTemplate(unittest.TestCase):

    def test_instantiate(self):
        # should pass without throwing any exceptions
        ServicesTemplate('TestTemplate', 'vpc-deadbeef', '10.0.0.0/8', 'rtb-deadbeef', ['subnet-cab4abba'])
