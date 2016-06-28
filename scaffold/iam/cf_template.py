import inspect
import json
import os

import troposphere.iam as iam
import troposphere as tp

from scaffold.template import TemplateBuilder


class IAMTemplate(TemplateBuilder):

    BUILD_PARM_NAMES = []

    def __init__(self, name,
                 description='[REPLACE ME]',
                 base_dir=None):
        super(IAMTemplate, self).__init__(name, description)
        if base_dir is None:
            base_dir = self._discover_basedir()
        self._base_dir = base_dir
        self._discover_policy_files()
        self._policies = {}

    def _discover_policy_files(self):
        self._policy_files = self._discover_files_under('policies')

    def _discover_basedir(self):
        return os.path.dirname(inspect.getfile(IAMTemplate))

    def _discover_files_under(self, dirname):
        files = []
        for (dirpath, dirnames, filenames) in os.walk(os.path.join(self._base_dir, dirname)):
            files.extend(os.path.join(dirpath, f) for f in filenames if f.endswith('.json'))
        return files

    def _resource_name(self, path):
        return os.path.basename(path).rsplit('.', 1)[0]

    def internal_build_template(self):
        self.create_policies()
        # self.create_roles()

    def create_policies(self):
        for policy_file in self._policy_files:
            with open(policy_file, 'r') as f:
                document = json.load(f)
            policy_name = self._resource_name(policy_file)
            resource_name = '{}Policy'.format(policy_name)
            policy = iam.ManagedPolicy(resource_name,
                                       PolicyDocument=document)
            self._policies[policy_name] = policy
            self.add_resource(policy)
            self.add_output(tp.Output(resource_name, Value=tp.Ref(policy)))

    def get_policy(self, policy_name):
        return self._policies[policy_name]


if __name__ == '__main__':
    template = IAMTemplate('testing')
    template.build_template()
    print template.to_json()
