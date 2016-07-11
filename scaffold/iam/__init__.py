from scaffold.stack.elements import Outputs


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
