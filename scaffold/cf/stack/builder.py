import os

from .operation import StackOperation
from .elements import Summary


class StackResults(object):
    def __init__(self, dry_run):
        self.dry_run = dry_run
        self.template = ''
        self.before_create = None
        self.stack_parameters = None
        self.stack = None
        self.after_create = None


class Dependencies(object):
    pass


class Parameters(object):
    pass


class ConfigUploader(object):

    def __init__(self, boto3_session, bucket_name):
        self._session = boto3_session
        self._bucket_name = bucket_name

    def upload_to_s3(self, base_dir, key_prefix, mapping={}):
        s3 = self._session.resource('s3')
        bucket = s3.Bucket(self._bucket_name)
        for dir_name, dir_list, file_list in os.walk(base_dir):
            for file_name in file_list:
                file_path = os.path.join(dir_name, file_name)
                target_path = os.path.relpath(file_path, base_dir)
                target_path = mapping.get(target_path, target_path)
                key_path = '/'.join((key_prefix, target_path))
                with open(file_path, 'r') as f:
                    bucket.put_object(Key=key_path,
                                      Body=f.read())


# TODO: use the new abstract method pattern with abc
class StackBuilder(object):
    def __init__(self, stack_name, boto3_session, is_update):
        self.stack_name = stack_name
        self.session = boto3_session
        self._is_update = is_update

    def build(self, dry_run=False):
        s3_key_prefix = self.create_s3_key_prefix()

        dependencies = Dependencies()
        dependencies.s3_key_prefix = s3_key_prefix
        self.get_dependencies(dependencies)

        build_parm_names = self.get_build_parameter_names()
        prev_build_parms = self.get_previous_build_parms(build_parm_names)

        template = self.create_template(dependencies, prev_build_parms)
        template.build_template()
        template_json = template.to_json()

        results = StackResults(dry_run)
        results.template = template_json
        results.before_create = self.do_before_create(dependencies, dry_run)

        stack_parms = self.get_stack_parameters()
        results.stack_parameters = stack_parms

        capabilities = self.get_capabilities()

        if dry_run:
            return results

        operator = StackOperation(self.session,
                                  self.stack_name,
                                  template_json,
                                  capabilities,
                                  self.get_s3_bucket(),
                                  s3_key_prefix)
        if self.is_update():
            results.stack = operator.update(stack_parms)
        else:
            results.stack = operator.create(stack_parms)
        results.after_create = self.do_after_create(results.stack)
        return results

    def get_previous_build_parms(self, names):
        p = Parameters()
        if self.is_update():
            summary = Summary(self.session, self.stack_name)
            p.description = summary.description()
            for name, value in summary.build_parameters().items():
                setattr(p, name, value)
        else:
            p.description = None
            for n in names:
                setattr(p, n, None)
        return p

    def is_update(self):
        return self._is_update

    def get_region(self):
        return self.session.region_name

    def get_s3_bucket(self):
        raise NotImplementedError('Must implement get_s3_bucket()')

    def create_s3_key_prefix(self):
        raise NotImplementedError('Must implement create_s3_key_prefix()')

    def create_template(self, dependencies):
        raise NotImplementedError('Must implement create_template')

    def get_build_parameter_names(self):
        return []

    def get_dependencies(self, dependencies):
        pass

    def do_before_create(self, dependencies, dry_run):
        pass

    def do_after_create(self, stack):
        pass

    def get_stack_parameters(self):
        return {}

    def get_capabilities(self):
        # Note: We could discover required capabilities automatically by querying the template for
        #       types that require capability acknowledgement. However, since Amazon requires explicit
        #       acknowledgement, we should require explicit acknowledgement as well. Therefore, subclasses
        #       should provide the appropriate capability if necessary.
        return []
