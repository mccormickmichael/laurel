import inspect
import os
import unittest

from scaffold.iam import discover_policy_files


class TestFileScanning(unittest.TestCase):

    def setUp(self):
        self.policy_dir = os.path.join(os.path.dirname(inspect.getfile(self.__class__)), 'policies')

    def test_discover_policy_files(self):
        '''Validate that all policy files are found, including subdirectories.
           Valid policy files are valid json.
           The test directory should be set up with an appropriate directory of policy files.
        '''
        file_mapping = discover_policy_files(self.policy_dir)
        self.assertIn('AllowAll', file_mapping)
        self.assertEqual(os.path.join(self.policy_dir, 'AllowAll.json'), file_mapping['AllowAll'])
        self.assertIn('AllS3', file_mapping)
