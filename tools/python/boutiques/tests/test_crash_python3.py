#!/usr/bin/env python

import os
import subprocess
import pytest
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh
from os.path import join as opj


class TestCrashPython3(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_no_container(self):
        command = ("bosh exec launch "
                   "{0} {1}".format(opj(self.get_examples_dir(),
                                        "crash3.json"),
                                    opj(self.get_examples_dir(),
                                        "crash3_invocation."
                                        + "json")))
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout = process.stdout.read().decode("utf-8").strip()
        self.assertIn("Could not pull Singularity image", stdout)
