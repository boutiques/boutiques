#!/usr/bin/env python

import subprocess

import pytest

from boutiques.bosh import bosh
from boutiques.tests.BaseTest import BaseTest


class TestInvocation(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("invocation")

    def test_invocation(self):
        descriptor = self.get_file_path("good.json")
        invocation = self.get_file_path("good_invocation.json")
        self.assertFalse(bosh(["invocation", descriptor, "-i", invocation, "-w"]))
        self.assertFalse(bosh(["invocation", descriptor, "-i", invocation, "-w"]))

    def test_invocation_json_obj(self):
        descriptor = open(self.get_file_path("good.json")).read()
        invocation = open(self.get_file_path("good_invocation.json")).read()
        self.assertFalse(bosh(["invocation", descriptor, "-i", invocation, "-w"]))
        self.assertFalse(bosh(["invocation", descriptor, "-i", invocation, "-w"]))

    def test_invocation_invalid_cli(self):
        descriptor = self.get_file_path("good.json")
        invocation = self.get_file_path("wrong_invocation.json")
        command = "bosh invocation " + descriptor + "-i " + invocation
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        process.communicate()
        self.assertTrue(process.returncode)
