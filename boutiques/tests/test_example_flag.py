#!/usr/bin/env python

import pytest

import boutiques as bosh
from boutiques.tests.BaseTest import BaseTest


class TestExampleFlag(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("example_flag")

    def test_example_flag_1(self):
        ret = bosh.execute("simulate",
                           self.get_file_path("example-flag.json"),
                           "-i",
                           self.get_file_path("i1.json"))
        self.assertEqual(ret.shell_command.strip(), "/bin/true -a -b")

    def test_example_flag_2(self):
        ret = bosh.execute("simulate",
                           self.get_file_path("example-flag.json"),
                           "-i",
                           self.get_file_path("i2.json"))
        self.assertEqual(ret.shell_command.strip(), "/bin/true")

    def test_example_flag_3(self):
        ret = bosh.execute("simulate",
                           self.get_file_path("example-flag.json"),
                           "-i",
                           self.get_file_path("i3.json"))

        self.assertEqual(ret.shell_command.replace("  ", " ").strip(),
                         "/bin/true -b")
