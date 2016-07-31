import os.path
from string import Template


class PolicySync(object):
    def __init__(self, boto3_session):
        self._session = boto3_session
        # Mocking out the session is sucky because we also have to mock out resources created by the session
        # What if we provided explicit aws clients or resources?

    def sync(self, policy_dir, dry_run):
        policy_variables = self._get_policy_variables()
        policy_file_dict = self._discover_policy_files(policy_dir)
        policy_text_dict = self._read_policy_files(policy_file_dict)
        self._resolve_variables(policy_text_dict, policy_variables)
        
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
        pass

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

    def _resolve_variables(self, policy_dict, variables):
        for policy, content in policy_dict.items():
            template = Template(content)
            policy_dict[policy] = template.safe_substitute(variables)

    def _get_policy_variables(self):
        '''Return a set of known variable substitutions:
           account_id
        '''
        # TODO: Fetching the account number is also done in the RoleSync class
        #       It should be abstracted out to someplace common
        #       How should we bypass or provide an alternate implementation
        #       
        return {}
