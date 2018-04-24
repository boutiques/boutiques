#!/usr/bin/env python

import os
import subprocess
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh


class TestExample2(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_example2_no_exec(self):
        example2_dir = os.path.join(self.get_examples_dir(), "example2")
        ret = bosh.execute("simulate",
                           os.path.join(example2_dir,
                                        "example2.json"),
                           "-i",
                           os.path.join(example2_dir,
                                        "invocation.json"))
        assert(ret.stdout == ""
               and ret.stderr == ""
               and ret.exit_code == 0
               and ret.error_message == "")

    def test_example2_exec(self):
        example2_dir = os.path.join(self.get_examples_dir(), "example2")
        ret = bosh.execute("launch",
                           os.path.join(example2_dir, "example2.json"),
                           os.path.join(example2_dir, "invocation.json"))
        assert(ret.stdout == b""
               and ret.stderr == b""
               and ret.exit_code == 0
               and ret.error_message == "")

        ret = bosh.execute("launch",
                           os.path.join(example2_dir, "example2.json"),
                           "-x",
                           os.path.join(example2_dir, "invocation.json"))
        print(ret)
        assert(ret.stdout == ""
               and ret.stderr == ""
               and ret.exit_code == 0
               and ret.error_message == "")

    def test_example2_no_exec_random(self):
        example2_dir = os.path.join(self.get_examples_dir(), "example2")
        self.assertFalse(bosh.execute("simulate",
                                      os.path.join(example2_dir,
                                                   "example2.json"),
                                      "-r", "3").exit_code)
