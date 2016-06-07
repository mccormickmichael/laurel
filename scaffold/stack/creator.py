
from .operation import StackOperation


class StackResults(object):
    def __init__(self, dry_run):
        self.dry_run = dry_run
        self.template = ''
        self.before_create = None
        self.stack = None
        self.after_create = None


class Dependencies(object):
    pass


# TODO: use the new abstract method pattern with abc
class StackCreator(object):
    def __init__(self, stack_name, boto3_session):
        self.stack_name = stack_name
        self.session = boto3_session

    def create(self, dry_run=False):
        s3_key_prefix = self.create_s3_key_prefix()

        dependencies = Dependencies()
        dependencies.s3_key_prefix = s3_key_prefix
        self.get_dependencies(dependencies)

        template = self.create_template(dependencies)
        template.build_template()
        template_json = template.to_json()

        results = StackResults(dry_run)
        results.template = template_json
        results.before_create = self.do_before_create(dependencies, dry_run)

        if dry_run:
            return results

        stack_parms = self.get_stack_parameters()
        creator = StackOperation(self.session,
                                 self.stack_name,
                                 template_json,
                                 self.get_s3_bucket(),
                                 s3_key_prefix)
        results.stack = creator.create(stack_parms)
        results.after_create = self.do_after_create(results.stack)
        return results

    def get_region(self):
        return self.session.region_name

    def get_s3_bucket(self):
        raise NotImplementedError('Must implement get_s3_bucket()')

    def create_s3_key_prefix(self):
        raise NotImplementedError('Must implement create_s3_key_prefix()')

    def create_template(self, dependencies):
        raise NotImplementedError('Must implement create_template')

    def get_dependencies(self, dependencies):
        pass

    def do_before_create(self, dependencies, dry_run):
        pass

    def do_after_create(self, stack):
        pass

    def get_stack_parameters(self):
        return {}
