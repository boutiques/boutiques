#!/usr/bin/env python

import os
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh


class TestSimulate(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_success(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.assertFalse(bosh.execute("simulate",
                                      os.path.join(example1_dir,
                                                   "example1_docker.json"),
                                      "-r", "1").exit_code)

        self.assertFalse(bosh.execute("simulate",
                                      os.path.join(self.get_examples_dir(),
                                                   "good_nooutputs.json"),
                                      "-r", "1").exit_code)

    def test_failing_bad_descriptor_invo_combos(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")

        self.assertRaises(SystemExit, bosh.execute, ["simulate",
                                                     os.path.join(example1_dir,
                                                                  "fake.json"),
                                                     "-i",
                                                     os.path.join(
                                                       example1_dir,
                                                       "invocation.json")])
        self.assertRaises(SystemExit, bosh.execute, ["simulate",
                                                     os.path.join(
                                                       example1_dir,
                                                       "example1_docker.json"),
                                                     "-i",
                                                     os.path.join(example1_dir,
                                                                  "fake.json")])
        self.assertRaises(SystemExit, bosh.execute, ["simulate",
                                                     os.path.join(
                                                       example1_dir,
                                                       "example1_docker.json"),
                                                     "-i",
                                                     os.path.join(
                                                       example1_dir,
                                                       "exampleTool1.py")])
        self.assertRaises(SystemExit, bosh.execute, ["simulate",
                                                     os.path.join(
                                                       example1_dir,
                                                       "example1_docker.json"),
                                                     "-r", "-2"])
        self.assertRaises(SystemExit, bosh.execute, ["simulate",
                                                     os.path.join(
                                                       example1_dir,
                                                       "example1_docker.json"),
                                                     "-r", "1", "-i",
                                                     os.path.join(
                                                       example1_dir,
                                                       "invocation.json")])
        self.assertRaises(SystemExit, bosh.execute, ["simulate",
                                                     os.path.join(
                                                       example1_dir,
                                                       "example1_docker.json")])

