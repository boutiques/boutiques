#!/usr/bin/env python

import subprocess

import pytest

from boutiques.tests.BaseTest import BaseTest


class TestCrashPython3(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("crash_python3")

    @pytest.mark.usefixtures("skip_if_no_apptainer")
    def test_no_container(self):
        command = "bosh exec launch --skip-data-collection " "{} {}".format(
            self.get_file_path("crash3.json"),
            self.get_file_path("crash3_invocation.json"),
        )
        print(command)
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout = process.stdout.read().decode("utf-8").strip()
        self.assertIn("Could not pull Singularity image", stdout)
