#!/usr/bin/env python

from boutiques.util.BaseTest import BaseTest
from boutiques import __file__ as bfile
import boutiques as bosh
import pytest
import os


class TestExample2(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup(os.path.join(os.path.dirname(bfile),
                                "schema", "examples", "example2"))

    def test_example2_validate(self):
        self.assertIsNone(bosh.validate(self.get_file_path("example2.json")))

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
                         self.get_file_path("invocation.json"),
                         "--skip-data-collection"),
            aditional_assertions=self.assert_no_output)

        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example2.json"),
                         "-x",
                         self.get_file_path("invocation.json"),
                         "--skip-data-collection"),
            aditional_assertions=self.assert_no_output)

    def test_example2_no_exec_random(self):
        self.assertFalse(
            bosh.execute("simulate",
                         self.get_file_path("example2.json")).exit_code)
