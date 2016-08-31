import inspect
import os.path
import unittest

from scaffold.iam.policy_sync import PolicySync


class TestPolicySync(unittest.TestCase):

    def setUp(self):
        self.mock_session = lambda: 0
        self.mock_session.resource = lambda r: r  # TODO: mock this out better. That it has to exist is stinky enough.
        self.policy_dir = os.path.join(os.path.dirname(inspect.getfile(TestPolicySync)), 'policies')

    def test_discover_policy_files(self):
        '''Validate that all policy files are found, including subdirectories.
           Valid policy files are valid json.
           The test directory should be set up with an appropriate directory of policy files.
        '''
        ps = PolicySync(self.mock_session)
        file_mapping = ps._discover_policy_files(self.policy_dir)
        self.assertIn('AllowAll', file_mapping)
        self.assertEqual(os.path.join(self.policy_dir, 'AllowAll.json'), file_mapping['AllowAll'])
        self.assertIn('AllS3', file_mapping)

    def test_read_policy_files(self):
        '''Validate that policy files are read.'''
        ps = PolicySync(self.mock_session)
        policy_file_map = ps._discover_policy_files(self.policy_dir)
        policy_text_map = ps._read_policy_files(policy_file_map)
        self.assertEqual(policy_file_map.keys(), policy_text_map.keys())
        for policy, filename in policy_file_map.items():
            with open(filename, 'r') as f:
                content = f.read()
                self.assertEqual(content, policy_text_map[policy],
                                 'Policy %(policy)s does not match contents of %(filename)s' % locals())
