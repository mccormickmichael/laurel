#!/usr/bin/python

import unittest
from troposphere import Ref
from .. import vpc

class TestVPCResources(unittest.TestCase):
    def test_should_create_vpc_cidr_block_as_ref(self):
        resource = vpc.create_vpc_with_inet_gateway('Blah', 'Block')['VPC']
        self.assertTrue(isinstance(resource.CidrBlock, Ref))

    def test_should_create_vpc_cidr_block_raw(self):
        block = '172.16.0.0/16'
        resource = vpc.create_vpc_with_inet_gateway('Blan', block)['VPC']
        self.assertEqual(block, resource.CidrBlock)
