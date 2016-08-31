import inspect
import os.path
import unittest

import troposphere.iam as iam

from scaffold.iam.cf_template import IAMTemplate
from scaffold.iam import discover_policy_files

class TestIAMTemplate(unittest.TestCase):

    def setUp(self):
        self.iam_doc_dir = os.path.dirname(inspect.getfile(self.__class__))
        self.template = IAMTemplate('TestTemplate', 'test-bucket',
                                    iam_doc_dir=self.iam_doc_dir)
        self.template.build_template()

    def test_policy_resource_name(self):
        resource_name = IAMTemplate._policy_res_name('Test')
        self.assertEqual('TestPolicy', resource_name)

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
        res = self.template.template.resources.get(IAMTemplate._policy_res_name(IAMTemplate.OUTPUT_NAME_BUCKET))
        self.assertIsNotNone(res)

    def test_should_add_policy_files_as_managed_policy_files(self):
        policy_files = discover_policy_files(self.template._policy_dir())
        for policy_name in policy_files.keys():
            res = self.template.template.resources.get(policy_name)
            self.assertIsNotNone(res)
            self.assertIsInstance(res, iam.ManagedPolicy)

    def test_should_add_policy_names_as_output(self):
        policy_files = discover_policy_files(self.template._policy_dir())
        for policy_name in policy_files.keys():
            output = self.template.template.outputs.get(IAMTemplate._policy_res_name(policy_name))
            self.assertIsNotNone(output)
