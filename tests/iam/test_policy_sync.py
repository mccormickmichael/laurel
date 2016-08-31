import inspect
import os.path
import unittest

from scaffold.iam.policy_sync import PolicySync
from scaffold.iam import discover_policy_files


class TestPolicySync(unittest.TestCase):

    def setUp(self):
        self.mock_session = lambda: 0
        self.mock_session.resource = lambda r: r  # TODO: mock this out better. That it has to exist is stinky enough.
        self.policy_dir = os.path.join(os.path.dirname(inspect.getfile(TestPolicySync)), 'policies')

    def test_read_policy_files(self):
        '''Validate that policy files are read.'''
        ps = PolicySync(self.mock_session)
        policy_file_map = discover_policy_files(self.policy_dir)
        policy_text_map = ps._read_policy_files(policy_file_map)
        self.assertEqual(policy_file_map.keys(), policy_text_map.keys())
        for policy, filename in policy_file_map.items():
            with open(filename, 'r') as f:
                content = f.read()
                self.assertEqual(content, policy_text_map[policy],
                                 'Policy %(policy)s does not match contents of %(filename)s' % locals())
