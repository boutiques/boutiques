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

    def test_example3_exec(self):
        example2_dir = os.path.join(self.get_examples_dir(), "example3")
        ret = bosh.execute("launch",
                           os.path.join(example2_dir, "example3.json"),
                           os.path.join(example2_dir, "invocation.json"))
        print(ret)
        assert(ret.stdout == "")  # if shell is not set to bash, this will fail
        assert(ret.stderr == "")
        assert(ret.exit_code == 0)
        assert(ret.error_message == "")
