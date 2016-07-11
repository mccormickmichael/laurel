import json
import logging

from . import load_policy_map, create_user_arns, create_role_arns


class RoleSync(object):
    def __init__(self, boto3_session,
                 iam_stack_name=None):
        self._session = boto3_session
        self._iam = self._session.resource('iam')
        self._policy_map = load_policy_map(boto3_session, iam_stack_name)

    def sync(self, roles_dict, dry_run):
        current_roles = [r for r in self._iam.roles.all() if not r.name.startswith('aws-')]  # exclude aws-generated roles

        defined_role_names = roles_dict.keys()
        current_role_names = [r.name for r in current_roles]

        logging.debug('current roles: {}'.format(sorted(current_role_names)))
        logging.debug('defined roles: {}'.format(sorted(defined_role_names)))

        roles_to_create = {r: roles_dict[r] for r in defined_role_names if r not in current_role_names}
        roles_to_delete = [r for r in current_roles if r.name not in defined_role_names]
        roles_to_update = [r for r in current_roles if r.name in defined_role_names]

        self.delete_roles(roles_to_delete, dry_run)
        self.create_roles(roles_to_create, dry_run)
        self.update_roles(roles_to_update, roles_dict, dry_run)

    def delete_roles(self, roles, dry_run):
        for role in roles:
            policies = role.attached_policies.all()
            for policy in policies:
                logging.info('detaching policy %s from role %s', policy.policy_name, role.name)
                if not dry_run:
                    role.detach_policy(PolicyArn=policy.arn)
            # TODO: look for Instance Profiles
            # TODO: look for Inline Policies
            logging.info('deleting role %s', role.name)
            if not dry_run:
                role.delete()

    def create_roles(self, roles, dry_run):
        for role_name, role_info in roles.items():
            assume_role_policy_doc = self._create_assumerolepolicydocument(role_info)
            logging.info('creating role %s', role_name)
            if not dry_run:
                role = self._iam.create_role(RoleName=role_name,
                                             AssumeRolePolicyDocument=assume_role_policy_doc)
                # TODO: call this even if dry-run flag is set, but pass something else
                policy_names_to_attach = role_info.get('Policies', [])
                self._attach_policies(role, policy_names_to_attach, dry_run)

    def update_roles(self, roles, roles_dict, dry_run):
        for role in roles:
            role_info = roles_dict[role.name]
            logging.info('updating role %s', role.name)
            logging.info('not updating role %s because unimplemented', role.name)

            assume_role_policy_doc = self._create_assumerolepolicydocument(role_info)
            if not dry_run:
                role.AssumeRolePolicy().update(assume_role_policy_doc)

            self._update_policies(role, role_info, dry_run)

    def _update_policies(self, role, role_dict, dry_run):
        role_policies = role.attached_policies.all()

        current_policy_names = [r.policy_name for r in role_policies]
        defined_policy_names = role_dict.get('Policies', [])

        policy_names_to_attach = [p for p in defined_policy_names if p not in current_policy_names]
        policy_names_to_detach = [p for p in current_policy_names if p not in defined_policy_names]

        self._detach_policies(role, policy_names_to_detach, dry_run)
        self._attach_policies(role, policy_names_to_attach, dry_run)

    def get_policy_arn(self, policy_name):
        return self._policy_map[policy_name]

    def _detach_policies(self, role, policy_names, dry_run):
        for policy_name in policy_names:
            logging.info('detaching policy %s from role %s', policy_name, role.name)
            if not dry_run:
                role.detach_policy(PolicyArn=self.get_policy_arn(policy_name))

    def _attach_policies(self, role, policy_names, dry_run):
        for policy_name in policy_names:
            logging.info('attaching policy %s to role %s', policy_name, role.name)
            if not dry_run:
                role.attach_policy(PolicyArn=self.get_policy_arn(policy_name))

    def _create_assumerolepolicydocument(self, role_info):
        principal = self._create_assume_role_principal(role_info['Principal'])
        document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "sts:AssumeRole",
                    "Principal": principal
                }
            ]
        }
        return json.dumps(document)

    def _create_assume_role_principal(self, principal):
        # special cases
        if principal.get('users') is not None:
            return {'AWS': create_user_arns(self._get_account_id(), principal.get('users'))}

        if principal.get('roles') is not None:
            return {'AWS': create_role_arns(self._get_account_id(), principal.get('roles'))}

        # otherwise, return principal unchanged. It's your fault if there are too many elements
        return principal

    def _get_account_id(self):
        # Not sure this is the best way to do it.
        return self._iam.CurrentUser().arn.split(':')[4]
