#!/usr/bin/env python

import os
import subprocess
from boutiques.tests.BaseTest import BaseTest
import boutiques as bosh


class TestExample2(BaseTest):

    def setUp(self):
        self.setup("example2")

    def test_example2_no_exec(self):
        self.assert_successful_return(
            bosh.execute("simulate",
                         self.get_file_path("example2.json"),
                         "-i",
                         self.get_file_path("invocation.json")),
            aditional_assertions=self.assert_only_stdout)

    def test_example2_exec(self):
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example2.json"),
                         self.get_file_path("invocation.json")),
            aditional_assertions=self.assert_no_output)

        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example2.json"),
                         "-x",
                         self.get_file_path("invocation.json")),
            aditional_assertions=self.assert_no_output)

    def test_example2_no_exec_random(self):
        self.assertFalse(
            bosh.execute("simulate",
                         self.get_file_path("example2.json")).exit_code)
