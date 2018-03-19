#!/usr/bin/env python

import os
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh

class TestExec(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_failing_launch(self):
        example1_dir = os.path.join(self.get_examples_dir(),"example1")       
        self.assertRaises(SystemExit, bosh.execute, ["launch",
                                                     os.path.join(example1_dir,
                                                                  "fake.json"),
                                                     os.path.join(example1_dir,
                                                                  "invocation.json")])
        self.assertRaises(SystemExit, bosh.execute, ["launch",
                                                     os.path.join(example1_dir,
                                                                  "example1.json"),
                                                     os.path.join(example1_dir,
                                                                  "fake.json")])
        self.assertRaises(SystemExit, bosh.execute, ["launch",
                                                     os.path.join(example1_dir,
                                                                  "example1.json"),
                                                     os.path.join(example1_dir,
                                                                  "exampleTool1.py")])

    def test_failing_simulate(self):
        example1_dir = os.path.join(self.get_examples_dir(),"example1")       
        self.assertRaises(SystemExit, bosh.execute, ["simulate",
                                                     os.path.join(example1_dir,
                                                                  "fake.json"),
                                                     "-i",
                                                     os.path.join(example1_dir,
                                                                  "invocation.json")])
        self.assertRaises(SystemExit, bosh.execute, ["simulate",
                                                     os.path.join(example1_dir,
                                                                  "example1.json"),
                                                     "-i",
                                                     os.path.join(example1_dir,
                                                                  "fake.json")])
        self.assertRaises(SystemExit, bosh.execute, ["simulate",
                                                     os.path.join(example1_dir,
                                                                  "example1.json"),
                                                     "-i",
                                                     os.path.join(example1_dir,
                                                                  "exampleTool1.py")])
        self.assertRaises(SystemExit, bosh.execute, ["simulate",
                                                     os.path.join(example1_dir,
                                                                  "example1.json"),
                                                     "-r", "-2"])
        self.assertFalse(bosh.execute("simulate",
                                      os.path.join(example1_dir,"example1.json"),
                                      "-r", "1"))
        self.assertRaises(SystemExit, bosh.execute, ["simulate",
                                                     os.path.join(example1_dir,
                                                                  "example1.json"),
                                                     "-r", "1", "-i",
                                                     os.path.join(example1_dir,
                                                                  "invocation.json")])
        self.assertRaises(SystemExit, bosh.execute, ["simulate",
                                                     os.path.join(example1_dir,
                                                                  "example1.json")])

