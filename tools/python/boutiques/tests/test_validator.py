#!/usr/bin/env python

from unittest import TestCase
from boutiques.bosh import bosh
from boutiques import __file__ as bfile
from boutiques.validator import DescriptorValidationError
import subprocess
import os.path as op
import os


class TestValidator(TestCase):

    def test_success(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/good.json')
        assert bosh(['validate', '--format', fil]) is None

    def test_success_cli(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/good.json')
        command = ("bosh validate " + fil)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout = process.stdout.read().decode("utf-8").strip()
        self.assertEqual(process.stderr.read().decode("utf-8").strip(), "")
        self.assertTrue(stdout == "OK")
        self.assertFalse(process.returncode)

    def test_fail(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/bad.json')
        self.assertRaises(DescriptorValidationError, bosh, ['validate', fil])

    def test_invalid_boutiques(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/invalid.json')
        self.assertRaises(DescriptorValidationError, bosh, ['validate', fil])

    def test_invalid_json(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/invalid_json.json')
        self.assertRaises(DescriptorValidationError, bosh, ['validate', fil])

    def test_invalid_json(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/test_exclusive_'
                                          'minimum.json')
        self.assertRaises(DescriptorValidationError, bosh, ['validate', fil])

    def test_invalid_cli(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/invalid.json')
        command = ("bosh validate " + fil)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate()
        self.assertTrue(process.returncode)

    def test_invalid_groups(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/invalid_groups.json')
        self.assertRaises(DescriptorValidationError, bosh, ['validate', fil])
