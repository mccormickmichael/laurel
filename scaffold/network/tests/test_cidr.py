#!/usr/bin/python

import unittest

from .. import cidr


class TestCidrUtils(unittest.TestCase):

    def test_to_mask_bits(self):
        bits = cidr._to_mask_bits(32)
        self.assertEqual(0xffffffff, bits)

    def test_to_ip_bits(self):
        bits = cidr._to_ip_bits((172, 16, 8, 0))
        self.assertEqual(0xac100800, bits)

    def test_block_size_to_mask_size(self):
        self.assertEqual(24, cidr._block_size_to_mask_size[256])


class TestCidrBlock(unittest.TestCase):

    def test_parse_block(self):
        cs = '172.16.8.0/21'
        cb = cidr.CidrBlock(cs)
        self.assertEqual('172.16.8.0', cb.ip_str())
        self.assertEqual(21, cb.mask_size())
        self.assertEqual('255.255.248.0', cb.mask_str())
        self.assertEqual(cs, str(cb))

    def test_internal_constructor(self):
        actual = cidr.CidrBlock(ip_bits=0xac100800, mask_size=20)
        expected = cidr.CidrBlock('172.16.8.0/20')
        self.assertEqual(expected, actual)

    def test_block_size(self):
        self.assertEqual(2048, cidr.CidrBlock('172.16.0.0/21').block_size())

    def test_equal(self):
        cb1 = cidr.CidrBlock('192.168.0.0/24')
        cb2 = cidr.CidrBlock('192.168.0.0/24')
        self.assertEqual(cb1, cb2)

    def test_not_equal_type(self):
        self.assertNotEqual(cidr.CidrBlock('192.168.1.0/24'), 'biggles')

    def test_not_equal(self):
        self.assertNotEqual(cidr.CidrBlock('192.168.1.0/24'), cidr.CidrBlock('192.168.0.0/24'))
        self.assertNotEqual(cidr.CidrBlock('192.168.1.0/24'), cidr.CidrBlock('192.168.1.0/20'))


class TestCidrBlockAllocator(unittest.TestCase):

    def setUp(self):
        self.cb = cidr.CidrBlock('10.0.0.0/8')
        self.ba = cidr.CidrBlockAllocator(self.cb)

    def test_string_constructor(self):
        cidr_s = '172.17.0.0/16'
        ba = cidr.CidrBlockAllocator(cidr_s)
        self.assertEquals(cidr.CidrBlock(cidr_s), ba._initial_block)

    def test_normalize_block_size_tiny(self):
        self.assertEqual(16, self.ba._normalize_block_size(1))

    def test_normalize_block_size_equal(self):
        self.assertEqual(32, self.ba._normalize_block_size(32))

    def test_normalize_block_size_too_big(self):
        size = 66000
        with self.assertRaises(ValueError) as cm:
            self.ba._normalize_block_size(size)
        self.assertTrue(str(size) in cm.exception.message)

    def test_free_ip_on_init(self):
        self.assertEqual(self.cb._ip_bits, self.ba._free_ip)

    def test_last_ip_on_init(self):
        expected = cidr._to_ip_bits((11, 0, 0, 0))
        self.assertEqual(expected, self.ba._exceed_ip)

    def test_simple_allocate(self):
        self.assertEqual(cidr.CidrBlock('10.0.0.0/24'), self.ba.alloc(256))

    def test_allocate_with_gap(self):
        self.ba.alloc(16)
        actual = self.ba.alloc(256)
        self.assertEqual(cidr.CidrBlock('10.0.1.0/24'), actual)

    def test_allocate_big_gap(self):
        self.ba.alloc(1024)
        actual = self.ba.alloc(2047)
        self.assertEqual(cidr.CidrBlock('10.0.8.0/21'), actual)

    def test_allocate_failure(self):
        ba = cidr.CidrBlockAllocator(cidr.CidrBlock('192.168.0.0/24'))
        with self.assertRaises(ValueError) as cm:
            ba.alloc(512)
        self.assertTrue('512 requested' in cm.exception.message)

    def test_allocate_fully(self):
        ba = cidr.CidrBlockAllocator(cidr.CidrBlock('192.168.0.0/24'))
        ba.alloc(128)
        ba.alloc(128)
        self.assertEqual(0xc0a80100, ba._free_ip)
