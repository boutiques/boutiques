#!/usr/bin/env python

import os
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh


class TestSurrChar(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_surr_char(self):
        ret = bosh.execute("simulate",
                           os.path.join(self.get_examples_dir(),
                                        "surr_char.json"),
                           "-i",
                           os.path.join(self.get_examples_dir(),
                                        "surr_char_inv.json"))
        self.assertIn("\"foo\"", ret.stdout)
        self.assertIn("%foo bar%", ret.stdout)
