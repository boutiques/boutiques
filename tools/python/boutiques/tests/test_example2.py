#!/usr/bin/env python

import os, subprocess
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh

class TestExample2(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_example2_no_exec(self):
        example2_dir = os.path.join(self.get_examples_dir(), "example2")       
        self.assertFalse(bosh.execute("simulate",
                                      os.path.join(example2_dir, "example2.json"),
                                      "-i",
                                      os.path.join(example2_dir, "invocation.json"))[2])

    def test_example2_exec(self):
        example2_dir = os.path.join(self.get_examples_dir(), "example2")       
        self.assertFalse(bosh.execute("launch",
                                      os.path.join(example2_dir, "example2.json"),
                                      os.path.join(example2_dir, "invocation.json"))[2])
        self.assertFalse(bosh.execute("launch",
                                      os.path.join(example2_dir, "example2.json"),
                                      "-x",
                                      os.path.join(example2_dir, "invocation.json"))[2])

    def test_example2_no_exec_random(self):
        example2_dir = os.path.join(self.get_examples_dir(), "example2")       
        self.assertFalse(bosh.execute("simulate",
                                      os.path.join(example2_dir, "example2.json"),
                                      "-r", "3")[2])