#!/usr/bin/env python

from unittest import TestCase
from boutiques.bosh import bosh
from boutiques import __file__ as bfile
from boutiques.validator import DescriptorValidationError
import subprocess
import os.path as op
import os
import simplejson as json


class TestExample(TestCase):

    def test_example_complete(self):
        descriptor = op.join(op.split(bfile)[0], 'schema/examples/'
                                                 'example-invocation/'
                                                 'example_descriptor.json')
        command = ("bosh example " + descriptor + " -c")
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        output = json.loads(process.stdout.read())

        self.assertDictEqual({"a1": "a1",
                              "b1": "b1", "b2": "b2",
                              "c1": "c1", "c2": "c2",
                              "d1": True, "d2": True}, output)

    def test_example_required_only(self):
        descriptor = op.join(op.split(bfile)[0], 'schema/examples/'
                                                 'example-invocation/'
                                                 'example_descriptor.json')
        command = ("bosh example " + descriptor)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        output = json.loads(process.stdout.read())

        self.assertDictEqual({"b1": "b1", "c2": "c2"}, output)

    def test_example_internal_validator_false_flag(self):
        self.maxDiff = None
        descriptor = op.join(op.split(bfile)[0], 'schema/examples/'
                                                 'example-invocation/'
                                                 'example_descriptor.json')
        invocation = op.join(op.split(bfile)[0], 'schema/examples/'
                                                 'example-invocation/'
                                                 'example_invocation.json')
        command = ("bosh exec simulate -i " + invocation + " " + descriptor)

        process = subprocess.Popen(command, shell=True,
                                   stderr=subprocess.PIPE)
        error = process.stderr.read().decode("utf-8")

        self.assertIn("d2 (False) flag is set to true or otherwise omitted",
                      error)
