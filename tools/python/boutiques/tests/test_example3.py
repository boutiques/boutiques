#!/usr/bin/env python

import os
import subprocess
from boutiques.tests.BaseTest import BaseTest
import boutiques as bosh


class TestExample2(BaseTest):

    def setUp(self):
        self.setup("example3")

    def test_example3_exec(self):
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example3.json"),
                         self.get_file_path("invocation.json")),
            aditional_assertions=self.assert_no_output)
