#!/usr/bin/env python

from boutiques.util.BaseTest import BaseTest
from boutiques import __file__ as bfile
import boutiques as bosh
import pytest
import os


class TestExample3(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup(os.path.join(os.path.dirname(bfile),
                                "schema", "examples", "example3"))

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
                         {'logfile': 'log-FileValue.txt'})
