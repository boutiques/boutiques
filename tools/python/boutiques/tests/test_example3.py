#!/usr/bin/env python

from boutiques.util.BaseTest import BaseTest
import boutiques as bosh


class TestExample3(BaseTest):

    def setUp(self):
        self.setup("example3")

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
