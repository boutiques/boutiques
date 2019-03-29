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
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.assertRaises(SystemExit, bosh.execute, ["launch",
                                                     os.path.join(example1_dir,
                                                                  "fake.json"),
                                                     os.path.join(
                                                       example1_dir,
                                                       "invocation.json"),
                                                     "--skip-data-collection"])
        self.assertRaises(SystemExit, bosh.execute, ["launch",
                                                     os.path.join(
                                                       example1_dir,
                                                       "example1_docker.json"),
                                                     os.path.join(example1_dir,
                                                                  "fake.json"),
                                                     "--skip-data-collection"])
        self.assertRaises(SystemExit, bosh.execute, ["launch",
                                                     os.path.join(
                                                       example1_dir,
                                                       "example1_docker.json"),
                                                     os.path.join(
                                                       example1_dir,
                                                       "exampleTool1.py"),
                                                     "--skip-data-collection"])
