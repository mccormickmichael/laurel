

class AmiRegionMap(dict):

    def __init__(self, more={}):
        self['us-east-1'] = {'GENERAL': 'ami-60b6c60a'}
        self['us-west-1'] = {'GENERAL': 'ami-d5ea86b5'}
        self['us-west-2'] = {'GENERAL': 'ami-f0091d91'}
        # TODO: add other regions
        # 'eu-west-1'
        # 'eu-central-1'
        # 'sa-east-1'
        # 'ap-southeast-1'
        # 'ap-southeast-2'
        # 'ap-northeast-1'
        # 'ap-northeast-2'
        self.add_map(more)

    def add_map(self, ami_map):
        '''Add a set of region => AMI mappings.

        ami_map -- a map of region => { name => ami_id } mappings. Example:
        {
          'us-east-1': {'NAT': 'ami-303b1458', 'BASTION': 'ami-60b6c60a'},
          'us-west-1': {'NAT': 'ami-7da94839', 'BASTION': 'ami-d5ea86b5'},
          'us-west-2': {'NAT': 'ami-69ae8259', 'BASTION': 'ami-f0091d91'}
        }
        '''
        for region, mapping in ami_map.items():
            if region in self:
                self[region].update(mapping)

    def add_ami_map(self, ami_name, region_to_ami_map):
        '''Add a set of AMI values to the AMI map.

        ami_name          -- the abstract name of the AMI (e.g. NAT, BASTION, LOGSTASH)
        region_to_ami_map -- a dict containing region => AMI value mapping. e.g.:
        { 'us-east-1': 'ami-60b6c60a',
          'us-west-1': 'ami-d5ea86b5',
          'us-west-2': 'ami-f0091d91'
        }
        '''
        for k, v in region_to_ami_map.items():
            if k in self:
                self[k][ami_name] = v
