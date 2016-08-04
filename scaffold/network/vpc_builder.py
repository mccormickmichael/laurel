from datetime import datetime

from .vpc_template import VpcTemplate
from ..stack.builder import StackBuilder


class VpcBuilder(StackBuilder):
    def __init__(self, args, session, is_update):
        super(VpcBuilder, self).__init__(args.stack_name, session, is_update)
        self.args = args

    def get_s3_bucket(self):
        return self.args.deploy_s3_bucket

    def create_s3_key_prefix(self):
        return '{}/vpc-{}'.format(self.args.deploy_s3_key_prefix, datetime.utcnow().strftime('%Y%m%d-%H%M%S'))

    def get_build_parameter_names(self):
        return list(VpcTemplate.BUILD_PARM_NAMES)

    def create_template(self, dependencies, build_parameters):
        return VpcTemplate(
            self.stack_name,
            region=self.get_region(),
            description=build_parameters.description if self.args.desc is None else self.args.desc,
            vpc_cidr=build_parameters.vpc_cidr if self.args.cidr is None else self.args.cidr,
            availability_zones=build_parameters.availability_zones if self.args.availability_zones is None else self.args.availability_zones,
            pub_size=build_parameters.pub_size if self.args.pub_size is None else self.args.pub_size,
            priv_size=build_parameters.priv_size if self.args.priv_size is None else self.args.priv_size
        )
