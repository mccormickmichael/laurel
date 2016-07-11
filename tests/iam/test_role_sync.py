import unittest

from scaffold.iam import create_user_arns


class TestRoleSync(unittest.TestCase):

    def test_create_user_arn_single(self):
        arns = create_user_arns('1234567890', 'biggles')
        self.assertIsInstance(arns, list)
        self.assertEqual(1, len(arns))
        self.assertEqual('arn:aws:iam::1234567890:user/biggles', arns[0])

    def test_create_user_arn_many(self):
        arns = create_user_arns('1234567890', ['john', 'eric', 'michael'])
        self.assertIsInstance(arns, list)
        self.assertEqual(3, len(arns))
        self.assertEqual('arn:aws:iam::1234567890:user/john', arns[0])
