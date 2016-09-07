import unittest

from scaffold.iam.role_sync import inline_cf_role_re, RoleSync


def mock_role(name):
    def mock(): lambda: 0
    mock.name = name
    return mock


class TestRoleSync(unittest.TestCase):

    def test_inline_cf_role_names(self):
        cf_name = 'Stack-Name-RoleNameRole-1BLAH7BLAH1BLAH'
        self.assertIsNotNone(inline_cf_role_re.match(cf_name))

    def test_not_inline_cf_role_names(self):
        not_cf_name = 'Regular-Role-Thing'
        self.assertIsNone(inline_cf_role_re.match(not_cf_name))

    def test_filter_current_roles_should_exclude_aws_roles(self):
        role_names = ['Inline-CloudFormationRole-BLAHBLAH',
                      'aws-role',
                      'MyRole'
                      ]
        roles = [mock_role(rn) for rn in role_names]
        filtered = RoleSync._filter_current_roles(roles)
        self.assertEqual(1, len(filtered))
        self.assertEqual('MyRole', filtered[0].name)
