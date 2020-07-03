#!/usr/bin/env python

from unittest import TestCase
from boutiques.bosh import bosh
import subprocess
import os.path as op
import simplejson as json
from boutiques import __file__ as bfile


class TestExample(TestCase):

    def test_reqInpGroup_nf_wGroup_OK(self):
        nf_desc = op.join(op.split(bfile)[0],
                          'schema/examples/naval_fate.json')
        invocation = op.join(op.split(bfile)[0],
                             'tests/docopt/naval_fate/nf_invoc_shoot.json')
        command = ("bosh invocation " + nf_desc + " -i " + invocation)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        self.assertEqual(process.stdout.read().strip(), b'OK')

    def test_reqInpGroup_nf_wOptionalFlag_OK(self):
        nf_desc = op.join(op.split(bfile)[0],
                          'schema/examples/naval_fate.json')
        invocation = op.join(op.split(bfile)[0],
                             'tests/docopt/naval_fate/nf_invoc_move.json')
        command = ("bosh invocation " + nf_desc + " -i " + invocation)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        self.assertEqual(process.stdout.read().strip(), b'OK')

    def test_reqInpGroup_nf_wChildren_woGroup_FAIL(self):
        nf_desc = op.join(op.split(bfile)[0],
                          'schema/examples/naval_fate.json')
        invocation = op.join(
            op.split(bfile)[0],
            'tests/docopt/naval_fate/nf_invoc_missing_group.json')
        command = ("bosh invocation " + nf_desc + " -i " + invocation)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        self.assertIn(b'Failed validating',
                      process.stdout.read().strip())

    def test_reqInpGroup_nf_woChildren_woGroup_FAIL(self):
        nf_desc = op.join(op.split(bfile)[0],
                          'schema/examples/naval_fate.json')
        invocation = op.join(
            op.split(bfile)[0],
            'tests/docopt/naval_fate/nf_invoc_missing_all.json')
        command = ("bosh invocation " + nf_desc + " -i " + invocation)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        self.assertIn(b'Failed validating',
                      process.stdout.read().strip())

    def test_reqInpGroup_valid_Complex_OK(self):
        valid_desc = op.join(op.split(bfile)[0],
                             'schema/examples/test_valid.json')
        invocation = op.join(
            op.split(bfile)[0],
            'tests/docopt/valid/valid_invoc_mutex.json')
        command = ("bosh invocation " + valid_desc + " -i " + invocation)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        self.assertEqual(process.stdout.read().strip(), b'OK')
