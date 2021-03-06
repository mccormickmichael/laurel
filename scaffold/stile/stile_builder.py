from datetime import datetime

from scaffold.cf.stack.builder import StackBuilder
from scaffold.cf import stack
from .stile_template import StileTemplate


class StileBuilder(StackBuilder):
    def __init__(self, args, session, is_update):
        super(StileBuilder, self).__init__(args.stack_name, session, is_update)
        self.args = args

    def get_s3_bucket(self):
        return self.args.deploy_s3_bucket

    def create_s3_key_prefix(self):
        return '{}/services-{}'.format(self.args.deploy_s3_key_prefix, datetime.utcnow().strftime('%Y%m%d-%H%M%S'))

    def get_build_parameter_names(self):
        return list(StileTemplate.BUILD_PARM_NAMES)

    def get_dependencies(self, dependencies):
        outputs = stack.outputs(self.session, self.args.network_stack_name)

        dependencies.vpc_id = outputs['VpcId']
        dependencies.vpc_cidr = outputs['VpcCidr']
        dependencies.priv_rt_id = outputs['PrivateRT']
        dependencies.public_subnet_ids = outputs.values(lambda k: 'PublicSubnet' in k)

        return dependencies

    def get_capabilities(self):
        # The service stack contains inline policy resources. Explicitly acknowledge it here.
        return ['CAPABILITY_IAM']

    def create_template(self, dependencies, build_parameters):
        return StileTemplate(
            self.stack_name,
            description=build_parameters.description if self.args.desc is None else self.args.desc,
            vpc_id=dependencies.vpc_id,
            vpc_cidr=dependencies.vpc_cidr,
            private_route_table_id=dependencies.priv_rt_id,
            public_subnet_ids=dependencies.public_subnet_ids,
            bastion_instance_type=build_parameters.bastion_type if self.args.bastion_type is None else self.args.bastion_type,
            nat_instance_type=build_parameters.nat_type if self.args.nat_type is None else self.args.nat_type
        )

    def get_stack_parameters(self):
        stack_parms = {}
        if self.args.bastion_key is not None:
            stack_parms[StileTemplate.BASTION_KEY_PARM_NAME] = self.args.bastion_key
        return stack_parms
