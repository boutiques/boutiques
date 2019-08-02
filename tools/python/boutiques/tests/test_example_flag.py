#!/usr/bin/env python

import os
import subprocess
import pytest
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh


class TestExampleFlag(TestCase):

    def test_example_flag_1(self):
        ex_dir = os.path.join(os.path.dirname(bfile),
                              "schema", "examples", "example-flag")
        ret = bosh.execute("simulate",
                           os.path.join(ex_dir, "example-flag.json"),
                           "-i",
                           os.path.join(ex_dir, "i1.json"))
        self.assertEqual(ret.shell_command.strip(), "/bin/true -a -b")

    def test_example_flag_2(self):
        ex_dir = os.path.join(os.path.dirname(bfile),
                              "schema", "examples", "example-flag")
        ret = bosh.execute("simulate",
                           os.path.join(ex_dir, "example-flag.json"),
                           "-i",
                           os.path.join(ex_dir, "i2.json"))
        self.assertEqual(ret.shell_command.strip(), "/bin/true")

    def test_example_flag_3(self):
        self.maxDiff = None
        ex_dir = os.path.join(os.path.dirname(bfile),
                              "schema", "examples", "example-flag")
        ret = bosh.execute("simulate",
                           os.path.join(ex_dir, "example-flag.json"),
                           "-i",
                           os.path.join(ex_dir, "i3.json"))

        self.assertEqual(ret.shell_command.replace("  ", " ").strip(),
                         "/bin/true -b")

    def test_example_flag_4(self):
        self.maxDiff = None
        test_desc = os.path.join(
            os.path.split(bfile)[0],
            'schema/examples/example-flag/example-flag.json')
        test_invocation = os.path.join(
            os.path.split(bfile)[0],
            'schema/examples/example-flag/i4.json')
        command = ("bosh exec simulate " +
                   test_desc + " -i " + test_invocation)

        process = subprocess.Popen(command, shell=True,
                                   stderr=subprocess.PIPE)
        stderr = process.stderr.read()[-60:].decode("utf-8").strip()
        self.assertTrue(
            "dash_b (False) flag is set to true or otherwise omitted" in
            stderr)
