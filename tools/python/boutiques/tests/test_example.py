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

        self.assertTrue(output["a1"] or output["a2"])
        self.assertDictContainsSubset({"b1": "b1", "b2": "b2", "c1": "c1",
                                       "c2": "c2"}, output)

    def test_example(self):
        descriptor = op.join(op.split(bfile)[0], 'schema/examples/'
                                                 'example-invocation/'
                                                 'example_descriptor.json')
        command = ("bosh example " + descriptor)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        output = json.loads(process.stdout.read())

        # Can't assert more than the required params because
        # params are randomly selected
        self.assertDictContainsSubset({"b1": "b1", "c2": "c2"}, output)
