import logging
import os.path

from . import matches_aws_policy_doc

logger = logging.getLogger('laurel.iam.PolicySync')


class PolicySync(object):
    def __init__(self, boto3_session):
        self._session = boto3_session
        self._iam = self._session.resource('iam')

    def sync(self, policy_dir, dry_run):
        policy_file_dict = self._discover_policy_files(policy_dir)
        policy_text_dict = self._read_policy_files(policy_file_dict)
        defined_policy_names = policy_file_dict.keys()

        current_policies = self._iam.policies.filter(Scope='Local')
        current_policy_names = [p.policy_name for p in current_policies]

        logger.debug('current policies: {}'.format(sorted(current_policy_names)))
        logger.debug('defined policies: {}'.format(sorted(defined_policy_names)))

        policies_to_create = [p for p in defined_policy_names if p not in current_policy_names]
        policies_to_delete = [p for p in current_policies if p.policy_name not in defined_policy_names]
        policies_to_update = [p for p in current_policies if p.policy_name in defined_policy_names]

        self._delete_policies(policies_to_delete, dry_run)
        self._create_policies(policies_to_create, policy_text_dict, dry_run)
        self._update_policies(policies_to_update, policy_text_dict, dry_run)
        
        # policies_to_update
        #  - delete last version if version count > 4
        #  - create new version
        #  - set current version to new version
        pass

    def _delete_policies(self, policies, dry_run):
        for policy in policies:
            logger.info('start delete policy %s', policy.policy_name)
            for group in policy.attached_groups.all():
                logger.info('detaching group %s', group.name)
                if not dry_run:
                    policy.detach_group(GroupName=group.name)
            for role in policy.attached_roles.all():
                logger.info('detaching role %s', role.name)
                if not dry_run:
                    policy.detach_role(RoleName=role.name)
            for user in policy.attached_users.all():
                logger.info('detaching user %s', user.name)
                if not dry_run:
                    policy.detach_user(UserName=user.name)
            for version in policy.versions.all():
                if not version.is_default_version:
                    logger.info('deleting version %s', version.version_id)
                    if not dry_run:
                        version.delete()
            logger.info('deleting policy %s', policy.policy_name)
            if not dry_run:
                policy.delete()

    def _create_policies(self, policy_names, policy_dict, dry_run):
        for name in policy_names:
            logger.info('creating policy %s', name)
            if not dry_run:
                self._iam.create_policy(PolicyName=name,
                                        PolicyDocument=policy_dict[name])

    def _update_policies(self, current_policies, policy_dict, dry_run):
        for policy in current_policies:
            policy_name = policy.policy_name
            defined_document = policy_dict[policy_name]
            current_document = policy.default_version.document
            if matches_aws_policy_doc(defined_document, current_document):
                logger.debug('policy %s has not changed. No need to update.', policy_name)
            else:
                logger.info('updating policy %s', policy_name)
                self._update_policy(policy, defined_document, True, dry_run)

    def _update_policy(self, policy, document, set_as_default, dry_run):
        versions = sorted(policy.versions.all(), key=lambda v: v.create_date)
        if len(versions) == 5:
            version_to_delete = next((v for v in versions if not v.is_default_version))
            logger.debug('deleting oldest version %s', version_to_delete.version_id)
            if not dry_run:
                version_to_delete.delete()
        logger.debug('creating new policy version')
        if not dry_run:
            policy.create_version(PolicyDocument=document,
                                  SetAsDefault=set_as_default)

    def _discover_policy_files(self, policy_dir):
        '''Return a {policy_name : file_path} mapping of all json files under policy_dir'''
        mapping = {}
        for (dirpath, dirnames, filenames) in os.walk(policy_dir):
            mapping.update(
                {
                    os.path.splitext(f)[0]:
                    os.path.join(dirpath, f) for f in filenames if f.endswith('.json')
                }
            )
        return mapping

    def _read_policy_files(self, policy_file_map):
        '''Return a dict of {policy_name: file_contents} given a mapping of {policy_name: file_path}'''
        contents = {}
        for policy, fn in policy_file_map.items():
            with open(fn, 'r') as f:
                contents[policy] = f.read()
        return contents
