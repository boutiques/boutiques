#!/usr/bin/env python

import os.path as op
import subprocess
import pytest
from boutiques.util.BaseTest import BaseTest
from boutiques import __file__ as bfile
import boutiques as bosh


class TestExampleFlag(BaseTest):

    def test_example_flag_1(self):
        ex_dir = op.join(self.tests_dir, "example-flag")
        ret = bosh.execute("simulate",
                           op.join(ex_dir, "example-flag.json"),
                           "-i",
                           op.join(ex_dir, "i1.json"))
        self.assertEqual(ret.shell_command.strip(), "/bin/true -a -b")

    def test_example_flag_2(self):
        ex_dir = op.join(self.tests_dir, "example-flag")
        ret = bosh.execute("simulate",
                           op.join(ex_dir, "example-flag.json"),
                           "-i",
                           op.join(ex_dir, "i2.json"))
        self.assertEqual(ret.shell_command.strip(), "/bin/true")

    def test_example_flag_3(self):
        ex_dir = op.join(self.tests_dir, "example-flag")
        ret = bosh.execute("simulate",
                           op.join(ex_dir, "example-flag.json"),
                           "-i",
                           op.join(ex_dir, "i3.json"))

        self.assertEqual(ret.shell_command.replace("  ", " ").strip(),
                         "/bin/true -b")
