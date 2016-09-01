
import json
import unittest

from .. import TemplateBuilder


class DummyTemplate(TemplateBuilder):

    BUILD_PARM_NAMES = ['string_parm', 'list_parm', 'int_parm']

    def __init__(self, name, description, string_parm, list_parm, int_parm):
        super(DummyTemplate, self).__init__(name, description, DummyTemplate.BUILD_PARM_NAMES)
        self.string_parm = string_parm
        self.list_parm = list_parm
        self.int_parm = int_parm


class TestBuildParameters(unittest.TestCase):

    def test_restore_parms(self):
        expected_string = 'thingy'
        expected_list = ['spam', 'eggs', 'bacon']
        expected_int = 123

        template_one = DummyTemplate('DummyOne', 'Description', expected_string, expected_list, expected_int)
        template_one.build_template()
        template_one_json = template_one.to_json()

        build_parameters = json.loads(template_one_json)['Metadata']['BuildParameters']
        template_two = DummyTemplate('DummyTwo', 'Description', 'bad', ['bad'], 0)
        template_two.restore_build_parms(build_parameters)

        self.assertEqual(expected_string, template_two.string_parm)
        self.assertEqual(expected_list, template_two.list_parm)
        self.assertEqual(expected_int, template_two.int_parm)
