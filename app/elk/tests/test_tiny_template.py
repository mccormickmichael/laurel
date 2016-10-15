
import unittest

from app.elk.tiny_template import TinyElkTemplate


class TestTinyElkTemplate(unittest.TestCase):

    def test_should_create_template(self):
        t = TinyElkTemplate('Testing',
                            region='us-west-2',
                            bucket='my_bucket',
                            bucket_key_prefix='my_bucket_prefix',
                            vpc_id='vpc-deadbeef',
                            vpc_cidr='10.0.0.0/16',
                            es_subnets=['subnet-deadbeef'],
                            description='Testing')
        t.build_template()
