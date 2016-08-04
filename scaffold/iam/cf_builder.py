from datetime import datetime

from .cf_template import IAMTemplate
from ..stack.builder import StackBuilder


class IAMBuilder(StackBuilder):
    def __init__(self, args, session, is_update):
        super(IAMBuilder, self).__init__(args.stack_name, session, is_update)
        self.args = args

    def get_s3_bucket(self):
        return self.args.deploy_s3_bucket

    def create_s3_key_prefix(self):
        return '{}/iam-{}'.format(self.args.deploy_s3_key_prefix, datetime.utcnow().strftime('%Y%m%d-%H%M%S'))

    def get_build_parameter_names(self):
        return list(IAMTemplate.BUILD_PARM_NAMES)

    def create_template(self, dependencies, build_parameters):
        return IAMTemplate(
            self.stack_name,
            description=build_parameters.description if self.args.desc is None else self.args.desc,
            s3_bucket_name=build_parameters.bucket_name if self.args.bucket is None else self.args.bucket,
            logging_enabled=build_parameters.logging_enabled if self.args.enable is None else self.args.enable,
        )
