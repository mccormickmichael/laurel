import unittest

from scaffold.iam import create_user_arns, matches_aws_policy_doc, deep_ordered


class TestMatchPolicyDoc(unittest.TestCase):
    def test_matches_policy_docs_simple(self):
        gen = '''{"Version": "2012-10-17", "Statement": [{"Action": "sts:AssumeRole", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::012345678901:user/biggles"}}]}'''
        aws = {'Version': '2012-10-17', 'Statement': [{'Action': 'sts:AssumeRole', 'Effect': 'Allow', 'Principal': {'AWS': 'arn:aws:iam::012345678901:user/biggles'}}]}
        self.assertTrue(matches_aws_policy_doc(aws, gen))

    def test_matches_policy_docs_unicode(self):
        gen = '''{"Version": "2012-10-17", "Statement": [{"Action": "sts:AssumeRole", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::012345678901:user/biggles"}}]}'''
        aws = {u'Version': u'2012-10-17', u'Statement': [{u'Action': u'sts:AssumeRole', u'Effect': u'Allow', u'Principal': {u'AWS': u'arn:aws:iam::012345678901:user/biggles'}}]}
        self.assertTrue(matches_aws_policy_doc(gen, aws))

    def test_matches_policy_docs_unordered(self):
        lhs = '''{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1462317982000",
            "Effect": "Allow",
            "Action": [
                "s3:AbortMultipartUpload",
                "s3:DeleteObject",
                "s3:GetObject",
                "s3:GetObjectAcl",
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::thousandleaves-web/*"
            ]
        }
    ]
}'''
        rhs = '''{
    "Statement": [
        {
            "Resource": [
                "arn:aws:s3:::thousandleaves-web/*"
            ],
            "Sid": "Stmt1462317982000",
            "Effect": "Allow",
            "Action": [
                "s3:DeleteObject",
                "s3:GetObject",
                "s3:PutObject",
                "s3:AbortMultipartUpload",
                "s3:PutObjectAcl",
                "s3:GetObjectAcl"
            ]
        }
    ],
    "Version": "2012-10-17"
}'''
        self.assertTrue(matches_aws_policy_doc(lhs, rhs))


class TestARNs(unittest.TestCase):

    def test_create_user_arn_single(self):
        arn = create_user_arns('1234567890', 'biggles')
        self.assertIsInstance(arn, basestring)
        self.assertEqual('arn:aws:iam::1234567890:user/biggles', arn)

    def test_create_user_arns_many(self):
        arns = create_user_arns('1234567890', ['john', 'eric', 'michael'])
        self.assertIsInstance(arns, list)
        self.assertEqual(3, len(arns))
        self.assertEqual('arn:aws:iam::1234567890:user/john', arns[0])

class TestDeepOrdered(unittest.TestCase):

    def test_simple_list(self):
        lhs = ['a', 'b', 'c']
        rhs = ['c', 'b', 'a']
        self.assertEqual(deep_ordered(lhs), deep_ordered(rhs))

    def test_simple_dict(self):
        # not sure if this one is valid because basic dictionary comparison works anyway.
        lhs = {'a': 'A', 'b': 'B', 'c': 'C'}
        rhs = {'c': 'C', 'b': 'B', 'a': 'A'}
        self.assertEqual(deep_ordered(lhs), deep_ordered(rhs))

    def test_nested_lists(self):
        lhs = ['a', ['b', 'c']]
        rhs = [['c', 'b'], 'a']
        self.assertEqual(deep_ordered(lhs), deep_ordered(rhs))

    def test_lists_in_dicts(self):
        lhs = {'a': 'A', 'b': ['B', 'c', 'C']}
        rhs = {'b': ['c', 'C', 'B'], 'a': 'A'}
        self.assertEqual(deep_ordered(lhs), deep_ordered(rhs))
