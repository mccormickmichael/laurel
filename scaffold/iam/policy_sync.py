

class PolicySync(object):
    def __init__(self, boto3_session):
        self._session = boto3_session

    def sync(self, policy_dir, dry_run):
        # read policy files
        # any processing? Replace known variables, such as ${account_id}. Leave ${aws:*} variables untouched
        #  t = string.Template(policy_document_body)
        #  t.safe_substitute(mapping, account_id=self.get_account_id_or_whatever) #or put account_id:account_id in the mapping
        # see https://docs.python.org/2/library/string.html#template-strings
        #   e.g. string.Template.safe_substitute
        # fetch existing policies
        # policies_to_delete
        # policies_to_create
        # policies_to_update
        #  - delete last version if version count > 4
        #  - create new version
        #  - set current version to new version
