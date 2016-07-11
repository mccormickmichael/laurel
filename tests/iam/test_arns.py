import unittest

from scaffold.iam import create_user_arns, matches_aws_policy_doc


class TestAssumeRolePolicyDocs(unittest.TestCase):
    def test_matches_aws_policy_docs_simple(self):
        gen = '''{"Version": "2012-10-17", "Statement": [{"Action": "sts:AssumeRole", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::012345678901:user/biggles"}}]}'''
        aws = {'Version': '2012-10-17', 'Statement': [{'Action': 'sts:AssumeRole', 'Effect': 'Allow', 'Principal': {'AWS': 'arn:aws:iam::012345678901:user/biggles'}}]}
        self.assertTrue(matches_aws_policy_doc(gen, aws))

    def test_matches_aws_policy_docs_unicode(self):
        gen = '''{"Version": "2012-10-17", "Statement": [{"Action": "sts:AssumeRole", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::012345678901:user/biggles"}}]}'''
        aws = {u'Version': u'2012-10-17', u'Statement': [{u'Action': u'sts:AssumeRole', u'Effect': u'Allow', u'Principal': {u'AWS': u'arn:aws:iam::012345678901:user/biggles'}}]}
        self.assertTrue(matches_aws_policy_doc(gen, aws))


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
