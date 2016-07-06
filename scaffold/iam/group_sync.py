import logging

from scaffold.stack.elements import Outputs


class GroupSync(object):
    def __init__(self, boto3_session,
                 iam_stack_name=None):
        self._session = boto3_session
        self._iam = self._session.resource('iam')
        self._load_policy_map(iam_stack_name)

    def sync(self, group_dict, dry_run):
        current_groups = self._iam.groups.all()

        defined_group_names = group_dict.keys()
        current_group_names = [g.name for g in current_groups]

        logging.info('current groups: {}'.format(sorted(current_group_names)))
        logging.info('defined groups: {}'.format(sorted(defined_group_names)))

        groups_to_create = [g for g in defined_group_names if g not in current_group_names]
        groups_to_update = [g for g in current_groups if g.name in defined_group_names]

        self.create_groups(groups_to_create, group_dict, dry_run)
        self.update_groups(groups_to_update, group_dict, dry_run)

    def create_groups(self, names, group_dict, dry_run):
        # TODO: honor dry_run parameter
        for name in names:
            policy_names = group_dict[name]
            logging.info('creating group {}'.format(name))
            group = self._iam.create_group(GroupName=name)
            for policy_name in policy_names:
                logging.info('attaching policy {} to group {}'.format(policy_name, name))
                group.attach_policy(PolicyArn=self.get_policy_arn(policy_name))

    def update_groups(self, groups, group_dict, dry_run):
        # TODO: honor dry_run parameter
        for group in groups:
            current_policies = group.attached_policies.all()

            defined_policy_names = group_dict[group.name]
            current_policy_names = [p.policy_name for p in current_policies]

            policy_arns_to_detach = [p.arn for p in current_policies
                                     if p.policy_name not in defined_policy_names]
            policy_names_to_attach = [p for p in defined_policy_names
                                      if p not in current_policy_names]

            for arn in policy_arns_to_detach:
                logging.info('detaching {} from group {}'.format(arn, group.name))
                group.detach_policy(PolicyArn=arn)
            for name in policy_names_to_attach:
                arn = self.get_policy_arn(name)
                logging.info('attaching {} to group {}'.format(arn, group.name))
                group.attach_policy(PolicyArn=arn)

    def get_policy_arn(self, policy_name):
        return self._policy_map[policy_name]

    def _load_policy_map(self, iam_stack_name):
        self._policy_map = {}
        for policy in self._iam.policies.all():
            self._policy_map[policy.policy_name] = policy.arn

        # also map IAM stack policy outputs to arns so we can use simple names
        # for policies created in the iam stack.
        if iam_stack_name is not None:
            cf = self._session.resource('cloudformation')
            iam_stack = cf.Stack(iam_stack_name)
            outputs = Outputs(iam_stack)
            for k in outputs.keys(key_filter=lambda x: x.endswith('Policy')):
                self._policy_map[k] = outputs[k]
