import troposphere as tp
import troposphere.autoscaling as autoscaling

from . import AmiRegionMap


def tags_to_dict(taglist):
    return {t['Key']: t['Value'] for t in taglist}


def retag(default_tags, **kwargs):
    """Add/replace tag objects; kwargs overrides existing tag values"""
    d = tags_to_dict(default_tags.tags)
    d.update(**kwargs)
    return tp.Tags(**d)


def asgtag(tags):
    """Turn regular cloudformation Tags into autoscaling Tags"""
    d = tags_to_dict(tags.tags)
    return autoscaling.Tags(**d)


def mergetag(a, b):
    """Merge Troposphere Tag objects. Dest values override src values."""
    d = tags_to_dict(a.tags + b.tags)
    return tp.Tags(**d)

BUILD_PARMS_NAME = 'BuildParameters'

REF_STACK_NAME = tp.Ref('AWS::StackName')
REF_REGION = tp.Ref('AWS::Region')

AMI_REGION_MAP_NAME = 'AMIRegionMap'
AMI_REGION_MAP = AmiRegionMap()


class TemplateBuilder(object):

    def __init__(self, name, description, build_parm_attrs=[]):
        self.name = name
        self.description = description
        self.default_tags = tp.Tags(Application=REF_STACK_NAME, Name=self.name)
        self.build_parm_attrs = build_parm_attrs

    def build_template(self):
        self._init_template()
        self._add_build_parms()
        self.internal_build_template()

    def to_json(self):
        return self.template.to_json()

    def add_metadata(self, key, meta_dict):
        meta = self.template.metadata or {}
        meta[key] = meta_dict
        self.template.add_metadata(meta)

    def add_mapping(self, mapping_name, mapping):
        self.template.add_mapping(mapping_name, mapping)

    def add_parameter(self, parameters):
        self.template.add_parameter(parameters)

    def add_resource(self, resource):
        self.template.add_resource(resource)

    def add_resources(self, *resources):
        self.add_resource(list(resources))

    def output(self, *outputs):
        '''Add an AWS object reference as an output. This is the most common use case.'''
        for o in outputs:
            self.output_ref(o.title, o)

    def output_ref(self, name, o):
        self.output_named(name, tp.Ref(o))

    def output_named(self, name, value):
        self.template.add_output(tp.Output(name, Value=value))

    def restore_build_parms(self, parms):
        for attr, value in parms.iteritems():
            setattr(self, attr, value)

    def internal_build_template(self):
        pass

    def internal_add_mappings(self):
        self.template.add_mapping(AMI_REGION_MAP_NAME, AMI_REGION_MAP)

    def _init_template(self):
        template = tp.Template()
        self.template = template
        template.add_version()
        template.add_description(self.description)
        self.internal_add_mappings()
        return template

    def _add_build_parms(self):
        parms_dict = {attr: getattr(self, attr) for attr in self.build_parm_attrs}
        self.add_metadata(BUILD_PARMS_NAME, parms_dict)

    def _rename(self, fmt):
        return retag(self.default_tags, Name=fmt.format(self.name))
