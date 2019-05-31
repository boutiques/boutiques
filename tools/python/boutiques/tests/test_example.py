#!/usr/bin/env python

from unittest import TestCase
from boutiques.bosh import bosh
from boutiques import __file__ as bfile
from boutiques.validator import DescriptorValidationError
import subprocess
import os.path as op
import os


class TestExample(TestCase):

    def test_example_complete_mutex_params(self):
        schema = op.join(op.split(bfile)[0], 'schema/examples/good.json')
        command = ("bosh example " + schema + " -c")
        process = subprocess.Popen(command, shell=True,
                                   stderr=subprocess.PIPE)
        expected = op.join(op.split(bfile)[0],
                           'schema/examples/good_invocation.json')
        process = subprocess.Popen(command, shell=True,
                                   stderr=subprocess.PIPE)
        print(expected)
