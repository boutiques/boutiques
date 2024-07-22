#!/usr/bin/env python

import os
import subprocess

import pytest

import boutiques as bosh
from boutiques import __file__ as bfile
from boutiques.tests.BaseTest import BaseTest


class TestExample3(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup(os.path.join(os.path.dirname(bfile),
                                "schema", "examples", "example3"))

    def test_example3_validate(self):
        self.assertIsNone(bosh.validate(self.get_file_path("example3.json")))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example3_exec(self):
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example3.json"),
                         self.get_file_path("invocation.json"),
                         "--skip-data-collection"),
            aditional_assertions=self.assert_no_output)

    def test_example3_filepathrenaming(self):
        self.assertEqual(bosh.evaluate(self.get_file_path("example3.json"),
                                       self.get_file_path("invocation.json"),
                                       "output-files/"),
                         {'logfile': './test_temp/log-FileValue.txt'})
