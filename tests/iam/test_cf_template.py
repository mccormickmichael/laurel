import unittest

from scaffold.iam.cf_template import IAMTemplate


class TestIAMTemplate(unittest.TestCase):

    def setUp(self):
        self.template = IAMTemplate('TestTemplate', 'test-bucket')
        self.template.build_template()

    def test_should_add_bucket_as_output(self):
        output = self.template.template.outputs.get(IAMTemplate.OUTPUT_NAME_BUCKET)
        self.assertIsNotNone(output)

    def test_should_add_trail_as_output(self):
        output = self.template.template.outputs.get(IAMTemplate.OUTPUT_NAME_TRAIL)
        self.assertIsNotNone(output)

    def test_should_add_bucket_as_resource(self):
        res = self.template.template.resources.get(IAMTemplate.OUTPUT_NAME_BUCKET)
        self.assertIsNotNone(res)

    def test_should_add_trail_as_resource(self):
        res = self.template.template.resources.get(IAMTemplate.OUTPUT_NAME_TRAIL)
        self.assertIsNotNone(res)

    def test_should_add_bucket_policy_as_resource(self):
        res = self.template.template.resources.get(IAMTemplate.OUTPUT_NAME_BUCKET + 'Policy')
        self.assertIsNotNone(res)
