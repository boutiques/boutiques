#!/usr/bin/env python

import subprocess

import pytest

from boutiques.tests.BaseTest import BaseTest


class TestExample(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("import/docopt/")

    def test_reqInpGroup_nf_wGroup_OK(self):
        nf_desc = self.get_file_path('naval_fate.json')
        invocation = self.get_file_path('nf_invoc_shoot.json')
        command = ("bosh invocation " + nf_desc + " -i " + invocation)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        self.assertEqual(process.stdout.read().strip(), b'OK')

    def test_reqInpGroup_nf_wOptionalFlag_OK(self):
        nf_desc = self.get_file_path('naval_fate.json')
        invocation = self.get_file_path('nf_invoc_move.json')
        command = ("bosh invocation " + nf_desc + " -i " + invocation)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        self.assertEqual(process.stdout.read().strip(), b'OK')

    def test_reqInpGroup_nf_wChildren_woGroup_FAIL(self):
        nf_desc = self.get_file_path('naval_fate.json')
        invocation = self.get_file_path('nf_invoc_missing_group.json')
        command = ("bosh invocation " + nf_desc + " -i " + invocation)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        self.assertIn(b'Failed validating',
                      process.stdout.read().strip())

    def test_reqInpGroup_nf_woChildren_woGroup_FAIL(self):
        nf_desc = self.get_file_path('naval_fate.json')
        invocation = self.get_file_path('nf_invoc_missing_all.json')
        command = ("bosh invocation " + nf_desc + " -i " + invocation)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        self.assertIn(b'Failed validating',
                      process.stdout.read().strip())

    def test_reqInpGroup_valid_Complex_OK(self):
        valid_desc = self.get_file_path('test_valid.json')
        invocation = self.get_file_path('valid_invoc_mutex.json')
        command = ("bosh invocation " + valid_desc + " -i " + invocation)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        self.assertEqual(process.stdout.read().strip(), b'OK')
