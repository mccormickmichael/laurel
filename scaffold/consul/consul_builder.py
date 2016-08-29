from datetime import datetime
import inspect
import os

from ..stack.builder import StackBuilder
from .. import stack
from .consul_template import ConsulTemplate


class ConsulBuilder(StackBuilder):
    def __init__(self, args, session, is_update):
        super(ConsulBuilder, self).__init__(args.stack_name, session, is_update)
        self.args = args

    def get_s3_bucket(self):
        return self.args.deploy_s3_bucket

    def create_s3_key_prefix(self):
        return '{}/consul-{}'.format(self.args.deploy_s3_key_prefix, datetime.utcnow().strftime('%Y%m%d-%H%M%S'))

    def get_dependencies(self, dependencies):
        outputs = stack.outputs(self.session, self.args.network_stack_name)

        dependencies.vpc_id = outputs['VpcId']
        dependencies.vpc_cidr = outputs['VpcCidr']
        dependencies.private_subnet_ids = outputs.values(lambda k: 'PrivateSubnet' in k)
        dependencies.public_subnet_ids = outputs.values(lambda k: 'PublicSubnet' in k)

    def get_capabilities(self):
        # The consul stack contains inline policy resources. Explicitly acknowledge it here.
        return ['CAPABILITY_IAM']

    def create_template(self, dependencies, build_parameters):
        args_dict = vars(self.args)  # convert to dict to handle missing arguments (e.g. from update jobs). Kind of icky.
        cluster_size = args_dict.get('cluster_size', build_parameters.cluster_size)
        instance_type = args_dict.get('instance_type', build_parameters.instance_type)
        ui_instance_type = args_dict.get('ui_instance_type', build_parameters.ui_instance_type)
        description = args_dict.get('desc', build_parameters.description)

        return ConsulTemplate(
            self.stack_name,
            region=self.get_region(),
            bucket=self.get_s3_bucket(),
            key_prefix=dependencies.s3_key_prefix,
            vpc_id=dependencies.vpc_id,
            vpc_cidr=dependencies.vpc_cidr,
            server_subnet_ids=dependencies.private_subnet_ids,
            ui_subnet_ids=dependencies.public_subnet_ids,  # TODO: user parameter to suppress UI instance.
            description=description,
            server_cluster_size=cluster_size,
            server_instance_type=instance_type,
            ui_instance_type=ui_instance_type
        )

    def do_before_create(self, dependencies, dry_run):
        base_dir = os.path.dirname(inspect.getfile(ConsulTemplate))
        base_dir = os.path.join(base_dir, 'config')

        s3 = self.session.resource('s3')
        bucket = s3.Bucket(self.get_s3_bucket())
        for dir_name, dir_list, file_list in os.walk(base_dir):
            for file_name in file_list:
                file_path = os.path.join(dir_name, file_name)
                key_path = '/'.join((dependencies.s3_key_prefix, os.path.relpath(file_path, base_dir)))
                with open(file_path, 'r') as f:
                    bucket.put_object(Key=key_path,
                                      Body=f.read())

    def get_stack_parameters(self):
        stack_parms = {}
        if self.args.consul_key is not None:
            stack_parms[ConsulTemplate.CONSUL_KEY_PARAM_NAME] = self.args.consul_key
        return stack_parms
