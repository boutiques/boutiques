#!/usr/bin/env python

import os, subprocess, pytest
from unittest import TestCase
from boutiques import __file__ as bfile
from boutiques import bosh

class TestExample1(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_example1_no_exec(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")       
        self.assertFalse(bosh(["exec", "simulate",
                               os.path.join(example1_dir, "example1.json"),
                               "-i",
                               os.path.join(example1_dir, "invocation.json")]))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(), reason="Docker not installed")
    def test_example1_exec(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")       
        self.assertFalse(bosh(["exec", "launch",
                               os.path.join(example1_dir, "example1.json"),
                               os.path.join(example1_dir, "invocation.json")]))
        self.assertFalse(bosh(["exec", "launch",
                               os.path.join(example1_dir, "example1.json"),
                               "-x",
                               os.path.join(example1_dir, "invocation.json")]))

    def test_example1_no_exec_random(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")       
        self.assertFalse(bosh(["exec", "simulate",
                               os.path.join(example1_dir, "example1.json"),
                               "-r", "-n", "3"]))
