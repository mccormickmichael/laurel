import unittest

import troposphere.iam as iam
import troposphere as tp

from scaffold.template import TemplateBuilder


class TestOutputs(unittest.TestCase):

    def setUp(self):
        self.tb = TemplateBuilder('Test', 'Testing')
        self.tb.build_template()

    def test_should_add_one_output(self):

        thing = iam.Group('TestGroup')
        self.tb.output(thing)
        t = self.tb.template

        self.assertIsNotNone(t.outputs.get('TestGroup'))

    def test_output_should_be_correct_type(self):

        thing = iam.Group('TestGroup')
        self.tb.output(thing)
        o = self.tb.template.outputs['TestGroup']

        self.assertIsInstance(o, tp.Output)

    def test_output_should_be_correct_value(self):
        thing = iam.Group('TestGroup')
        self.tb.output(thing)
        o = self.tb.template.outputs['TestGroup']

        self.assertEqual(thing.title, o.title)

    def test_should_add_many_outputs(self):
        thing_one = iam.Group('TestGroupOne')
        thing_two = iam.Group('TestGroupTwo')
        self.tb.output(thing_one, thing_two)
        t = self.tb.template

        self.assertEqual(2, len(t.outputs))
        self.assertIsNotNone(t.outputs.get('TestGroupOne'))
        self.assertIsNotNone(t.outputs.get('TestGroupTwo'))

    def test_named_output(self):
        thing = iam.Group('TestGroup')
        self.tb.output_named('argle', tp.Ref(thing))

        self.assertIsNotNone(self.tb.template.outputs.get('argle'))

    def test_output_reference(self):
        thing = iam.Group('TestGroup')
        self.tb.output_ref('argle', thing)
        o = self.tb.template.outputs['argle']

        self.assertIsInstance(o.Value, tp.Ref)
