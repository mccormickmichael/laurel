from datetime import datetime
import inspect
import os

from scaffold.cf.stack.builder import StackBuilder, ConfigUploader
from scaffold.cf import stack
from .tiny_template import TinyElkTemplate


class TinyElkBuilder(StackBuilder):
    def __init__(self, args, session, is_update):
        super(TinyElkBuilder, self).__init__(args.stack_name, session, is_update)
        self.args = args

    def get_s3_bucket(self):
        return self.args.deploy_s3_bucket

    def create_s3_key_prefix(self):
        return '{}/elk-tiny-{}'.format(self.args.deploy_s3_key_prefix, datetime.utcnow().strftime('%Y%m%d-%H%M%S'))

    def get_dependencies(self, dependencies):
        outputs = stack.outputs(self.session, self.args.network_stack_name)

        dependencies.vpc_id = outputs['VpcId']
        dependencies.vpc_cidr = outputs['VpcCidr']
        dependencies.es_subnet_ids = outputs.values(lambda k: 'PrivateSubnet' in k)
        # dependencies.kibana_subnet_ids = outputs.values(lambda k: 'PublicSubnet' in k)

    def get_capabilities(self):
        # The elk stack contains inline policy resources. Explicitly acknowledge it here.
        return ['CAPABILITY_IAM']

    def get_build_parameter_names(self):
        return TinyElkTemplate.BUILD_PARM_NAMES

    def create_template(self, dependencies, build_parameters):
        argy = self.args

        return TinyElkTemplate(
            self.stack_name,
            region=self.get_region(),
            bucket=self.get_s3_bucket(),
            bucket_key_prefix=dependencies.s3_key_prefix,
            vpc_id=dependencies.vpc_id,
            vpc_cidr=dependencies.vpc_cidr,
            es_subnets=build_parameters.es_subnets if build_parameters.es_subnets else dependencies.es_subnet_ids,
            description=build_parameters.description if argy.desc is None else argy.desc
        )
    # kibana_subnet_ids=dependencies.kibana_subnet_ids,
    # es_instance_type=build_parameters.es_instance_type if argy.es_instance_type is None else argy.es_instance_type,
    # kibana_instance_type=build_parameters.kibana_instance_type if argy.kibana_instance_type is None else argy.kibana_instance_type

    def do_before_create(self, dependencies, dry_run):
        base_dir = os.path.dirname(inspect.getfile(TinyElkTemplate))
        base_dir = os.path.join(base_dir, 'config')

        ConfigUploader(self.session, self.get_s3_bucket()).upload_to_s3(base_dir, dependencies.s3_key_prefix)

    def get_stack_parameters(self):
        stack_parms = {}
        if self.args.server_key is not None:
            stack_parms[TinyElkTemplate.SERVER_KEY_PARM_NAME] = self.args.server_key
        return stack_parms
