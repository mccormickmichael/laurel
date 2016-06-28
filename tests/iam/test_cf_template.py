import inspect
import os
import unittest

import troposphere.iam as iam

from scaffold.iam.cf_template import IAMTemplate


def list_json_files(basedir):
    paths = []
    for (dirpath, dirnames, filenames) in os.walk(basedir):
        paths.extend(os.path.join(dirpath, f) for f in filenames if f.endswith('.json'))
    return paths


class TestIAMTemplate(unittest.TestCase):

    def _test_dir(self, dirname):
        return os.path.join(self._base_dir(), dirname)

    def _base_dir(self):
        return os.path.dirname(inspect.getfile(self.__class__))

    def setUp(self):
        self.template = IAMTemplate('Testing', base_dir=self._base_dir())
        self.template.build_template()

    def test_discover_basedir(self):
        expected_dir = os.path.dirname(inspect.getfile(IAMTemplate))
        template = IAMTemplate('Testing')
        self.assertEqual(expected_dir, template._discover_basedir())

    def test_discover_policy_files(self):
        expected_files = sorted(list_json_files(self._test_dir('policies')))

        template = IAMTemplate('Testing', base_dir=self._base_dir())
        template._discover_policy_files()
        actual_files = sorted(template._policy_files)

        self.assertEqual(expected_files, actual_files)

    def test_resource_name_should_match_file_name_from_path(self):
        resource_name = self.template._resource_name('/path/to/resource.name')
        self.assertEqual('resource', resource_name)

    def test_should_create_policy_resource(self):
        policy = self.template.get_policy('alls3')
        self.assertIsNotNone(policy)

    def test_should_add_policy_as_resource(self):
        resource = self.template.template.resources.get('alls3Policy')
        self.assertIsNotNone(resource)

    def test_should_add_policy_as_output(self):
        output = self.template.template.outputs.get('alls3Policy')
        self.assertIsNotNone(output)

    def test_all_policies_should_be_managed_policies(self):
        policies = [v for k, v in self.template.template.resources.items() if k.endswith('Policy')]
        for p in policies:
            self.assertIsInstance(p, iam.ManagedPolicy, 'Policy named {} should be of type {} but was {}'.format(p.title, iam.ManagedPolicy, p.__class__))
