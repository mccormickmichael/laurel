import logging

logger = logging.getLogger('laurel.iam.UserSync')


class UserSync(object):
    def __init__(self, boto3_session):
        self._session = boto3_session
        self._iam = self._session.resource('iam')

    def sync(self, user_dict, dry_run):
        current_users = self._iam.users.all()

        defined_user_names = user_dict.keys()
        current_user_names = [u.name for u in current_users]

        logger.info('current users: {}'.format(sorted(current_user_names)))
        logger.info('defined users: {}'.format(sorted(defined_user_names)))

        users_to_create = [u for u in defined_user_names if u not in current_user_names]
        users_to_update = [u for u in current_users if u.name in defined_user_names]

        self.create_users(users_to_create, user_dict, dry_run)
        self.update_users(users_to_update, user_dict, dry_run)

    def create_users(self, names, user_dict, dry_run):
        # TODO: honor dry_run parameter
        for name in names:
            logger.info('creating user {}'.format(name))
            user = self._iam.create_user(UserName=name)
            group_names = user_dict[name]
            for group_name in group_names:
                logger.info('adding {} to group {}'.format(name, group_name))
                user.add_group(GroupName=group_name)

    def update_users(self, users, user_dict, dry_run):
        # TODO: honor dry_run parameter
        for user in users:
            current_groups = user.groups.all()

            defined_group_names = user_dict[user.name]
            current_group_names = [g.name for g in current_groups]

            group_names_to_remove = [g.name for g in current_groups
                                     if g.name not in defined_group_names]
            group_names_to_add = [g for g in defined_group_names
                                  if g not in current_group_names]

            for name in group_names_to_remove:
                logger.info('removing group {} from user {}'.format(name, user.name))
                user.remove_group(GroupName=name)
            for name in group_names_to_add:
                logger.info('adding group {} to user {}'.format(name, user.name))
                user.add_group(GroupName=name)
