import json
import types

from scaffold.cf.stack.elements import Outputs


def load_policy_map(boto3_session, iam_stack_name=None):
    policy_map = {}
    iam = boto3_session.resource('iam')
    for policy in iam.policies.all():
        policy_map[policy.policy_name] = policy.arn

    # also map IAM stack policy outputs to arns so we can use simple names
    # for policies created in the iam stack.
    if iam_stack_name is not None:
        cf = boto3_session.resource('cloudformation')
        iam_stack = cf.Stack(iam_stack_name)
        outputs = Outputs(iam_stack)
        for k in outputs.keys(key_filter=lambda x: x.endswith('Policy')):
            policy_map[k] = outputs[k]

    return policy_map


def matches_aws_policy_doc(lhs, rhs):
    # assume anything that's a string is serialized json.
    if isinstance(lhs, types.StringTypes):
        lhs = json.loads(lhs)
    if isinstance(rhs, types.StringTypes):
        rhs = json.loads(rhs)
    return deep_ordered(lhs) == deep_ordered(rhs)


def create_user_arns(account_id, users):
    return create_iam_arns(account_id, 'user', users)


def create_role_arns(account_id, roles):
    return create_iam_arns(account_id, 'role', roles)


def create_iam_arns(account_id, prefix, items):
    if isinstance(items, basestring):
        items = [items]
    arns = ['arn:aws:iam::{}:{}/{}'.format(account_id, prefix, i) for i in items]
    # 1-element arn lists are stripped by AWS, we should do the same.
    if len(arns) == 1:
        return arns[0]
    return arns


def deep_ordered(obj):
    '''Deep orders nested dicts and lists (e.g. parsed json) so they can be compared.'''
    if isinstance(obj, dict):
        return sorted((k, deep_ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(deep_ordered(x) for x in obj)
    return obj
