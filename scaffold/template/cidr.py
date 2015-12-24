#!/usr/bin/python

import re

_block_size_to_mask_size = {
    int(1 << n): (32 - n) for n in range(4, 17)
}
_normal_block_sizes = sorted(_block_size_to_mask_size.keys())


def _to_quad(bits):
    """Create a 4-element tuple of integers from a 32-bit integer"""
    return ( (bits & 0xff000000) >> 24, (bits & 0xff0000) >> 16, (bits & 0xff00) >> 8, bits & 0xff )

def _parse_quad_str(s):
    """Parse a string of the form xxx.x.xx.xxx to a 4-element tuple of integers"""
    return tuple(int(q) for q in s.split('.'))

def _format_quad_str(quad):
    """Format a 4-element tuple of integers into a string of the form xxxx.xx.x.xxx"""
    return '{}.{}.{}.{}'.format(*quad)

def _to_ip_bits(quad):
    """Turn a 4-element tuple of integers into a 32-bit integer"""
    return quad[0] << 24 | quad[1] << 16 | quad[2] << 8 | quad[3]

def _to_mask_bits(size):
    """Create a 32-bit integer representing a mask of the given # of bits"""
    mb = 0
    for bs in range(31, 31 - size, -1):
        mb = mb | 1 << bs
    return mb

CIDR_RE = re.compile(r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$")

class CidrBlock(object):
    def __init__(self, cidr_str = None, **kwargs):
        if cidr_str is not None:
            self.__init_str(cidr_str)
        else:
            self.__init_thing(kwargs['ip_bits'],kwargs['mask_size'])

    def __init_str(self, cidr_str):
        if not CIDR_RE.match(cidr_str):
            raise ValueError('{} is not a valid cidr block expression'.format(cidr_str))
        elements = cidr_str.split('/')
        quad = _parse_quad_str(elements[0])

        self._mask_size = int(elements[1])
        self._ip_bits = _to_ip_bits(quad)
        self._mask_bits = _to_mask_bits(self._mask_size)

    def __init_thing(self, ip_bits, mask_size):
        self._mask_size = mask_size
        self._ip_bits = ip_bits
        self._mask_bits = _to_mask_bits(self._mask_size)

    def __str__(self):
        return '{}/{}'.format(self.ip_str(), self.mask_size())

    def __repr__(self):
        return 'CidrBlock({})'.format(self.__str__())

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                other._ip_bits == self._ip_bits and
                other._mask_size == self._mask_size)

    def ip_str(self):
        return _format_quad_str(self._ip_quad())

    def mask_size(self):
        return self._mask_size

    def block_size(self):
        return 1 << (32 - self.mask_size())

    def mask_str(self):
        return _format_quad_str(_to_quad(self._mask_bits))

    def _ip_quad(self):
        return _to_quad(self._ip_bits)

    def _mask_quad(self):
        return _to_quad(self._mask_bits)

    

class CidrBlockAllocator(object):
    def __init__(self, initial_block):
        self._initial_block = initial_block
        self._free_ip = initial_block._ip_bits
        self._exceed_ip = self._free_ip + (1 << (32 - initial_block._mask_size))

    def alloc(self, requested_block_size):
        block_size = self._normalize_block_size(requested_block_size)
        mask_size = _block_size_to_mask_size[block_size]
        mask = _to_mask_bits(mask_size)

        next_ip = self._free_ip + (block_size - 1) & mask
        next_free_ip = next_ip + block_size
        if next_free_ip > self._exceed_ip:
            raise ValueError('less than {} free ips available ({} requested)'.format(block_size, requested_block_size))
        
        self._free_ip = next_free_ip
        return CidrBlock(ip_bits = next_ip, mask_size = mask_size)

    def _normalize_block_size(self, block_size):
        for ns in _normal_block_sizes:
            if block_size <= ns:
                return ns
        raise ValueError('block size must be <= {} ({} given)'.format(max(_normal_block_sizes), block_size))
