#!/usr/bin/env python

from boutiques.bosh import bosh
from boutiques import __file__ as bfile
from boutiques.validator import DescriptorValidationError
import subprocess
import os.path as op
import os
from boutiques.tests.BaseTest import BaseTest
import pytest


class TestValidator(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("validator")

    def test_success(self):
        self.setup("invocation")
        fil = self.get_file_path('good.json')
        self.assertIsNone(bosh(['validate', '--format', fil]))

    def test_success_cli(self):
        self.setup("invocation")
        fil = self.get_file_path('good.json')
        command = ("bosh validate " + fil)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout = process.stdout.read().decode("utf-8").strip()
        self.assertEqual(stdout, "OK")
        self.assertFalse(process.returncode)

    def test_fail(self):
        fil = self.get_file_path('bad.json')
        self.assertRaises(DescriptorValidationError, bosh, ['validate', fil])

    def test_invalid_boutiques(self):
        fil = self.get_file_path('invalid.json')
        self.assertRaises(DescriptorValidationError, bosh, ['validate', fil])

    def test_invalid_json_debug(self):
        fil = self.get_file_path('invalid_json.json')
        command = ("bosh validate " + fil)
        process = subprocess.Popen(command, shell=True,
                                   stderr=subprocess.PIPE)
        stderr = process.stderr.read()[-59:].decode("utf-8").strip()
        self.assertEqual(stderr, 'Expecting \',\' delimiter or \'}\': line 9' +
                         ' column 2 (char 243)')

    def test_invalid_json(self):
        fil = self.get_file_path('test_exclusive_minimum.json')
        self.assertRaises(DescriptorValidationError, bosh, ['validate', fil])

    def test_invalid_cli(self):
        fil = self.get_file_path('invalid.json')
        command = ("bosh validate " + fil)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate()
        self.assertTrue(process.returncode)

    def test_invalid_groups(self):
        fil = self.get_file_path('invalid_groups.json')
        self.assertRaises(DescriptorValidationError, bosh, ['validate', fil])

    def test_invalid_container_index(self):
        fil = self.get_file_path('test_conIndexImage.json')
        command = ("bosh validate " + fil)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        stdout = process.stdout.read().decode("utf-8").strip()
        self.assertIn('ContainerError: container image'
                      ' \"docker://index.docker.io\" is prepended by index'
                      ' that doesn\'t match container index value'
                      ' \"shub://\"', stdout)
