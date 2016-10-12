import unittest

from scaffold.cf import AmiRegionMap


class TestAmiRegionMap(unittest.TestCase):

    def test_add_single_region_mapping(self):
        ami_map = AmiRegionMap()
        ami_map.add_ami_map('BIGGLES', {'us-east-1': 'ami-deadbeef'})
        self.assertEqual('ami-deadbeef', ami_map['us-east-1']['BIGGLES'])

    def test_add_to_one_region_not_in_another(self):
        ami_map = AmiRegionMap()
        ami_map.add_ami_map('BIGGLES', {'us-east-1': 'ami-deadbeef'})
        self.assertNotIn('BIGGLES', ami_map['us-west-1'])

    def test_add_bogus_region(self):
        ami_map = AmiRegionMap()
        ami_map.add_ami_map('BIGGLES', {'anthrax': 'ami-deadbeef'})
        self.assertNotIn('anthrax', ami_map)

    def test_add_full_mapping(self):
        ami_map = AmiRegionMap()
        stile_map = {
          'us-east-1': {'NAT': 'ami-303b1458', 'BASTION': 'ami-60b6c60a'},
          'us-west-1': {'NAT': 'ami-7da94839', 'BASTION': 'ami-d5ea86b5'},
          'us-west-2': {'NAT': 'ami-69ae8259', 'BASTION': 'ami-f0091d91'}
        }
        ami_map.add_map(stile_map)
        self.assertEquals('ami-69ae8259', ami_map['us-west-2']['NAT'])
        self.assertEquals('ami-d5ea86b5', ami_map['us-west-1']['BASTION'])
