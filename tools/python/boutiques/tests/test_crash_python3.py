#!/usr/bin/env python

import os
import subprocess
import pytest
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh
from os.path import join as opj
from boutiques.util.BaseTest import BaseTest


class TestCrashPython3(BaseTest):

    def test_no_container(self):
        command = ("bosh exec launch --skip-data-collection "
                   "{0} {1}".format(opj(self.schema_examples_dir,
                                        "crash_python3",
                                        "crash3.json"),
                                    opj(self.schema_examples_dir,
                                        "crash_python3",
                                        "crash3_invocation.json")))
        print(command)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout = process.stdout.read().decode("utf-8").strip()
        self.assertIn("Could not pull Singularity image", stdout)
