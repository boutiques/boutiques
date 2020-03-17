#!/usr/bin/env python

import os
import subprocess
import pytest
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh


class TestNoContainer(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_no_container(self):
        self.assertFalse(bosh.execute("launch",
                                      os.path.join(self.get_examples_dir(),
                                                   "no_container.json"),
                                      os.path.join(self.get_examples_dir(),
                                                   "no_container_invocation."
                                                   + "json"),
                                      "--skip-data-collection").exit_code)

    def test_bare_metal_execution(self):
        e = bosh.execute("launch", "--no-container",
                         os.path.join(self.get_examples_dir(),
                                      "baremetal", "test_baremetal.json"),
                         os.path.join(self.get_examples_dir(),
                                      "baremetal", "test_baremetal_invoc.json"))
        stdout = e.stdout
        if os.path.exists("test_baremetal_exec.txt"):
            os.remove("test_baremetal_exec.txt")
        self.assertEqual(stdout, "Bare metal execution\n")
