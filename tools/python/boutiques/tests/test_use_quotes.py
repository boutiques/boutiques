#!/usr/bin/env python

import os
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh


class TestUseQuotes(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_use_quotes(self):
        ret = bosh.execute("simulate",
                           os.path.join(self.get_examples_dir(),
                                        "use_quotes.json"),
                           "-i",
                           os.path.join(self.get_examples_dir(),
                                        "use_quotes_inv.json"))
        self.assertIn("\"'f\\\"oo'\"", ret.stdout)
        self.assertIn("\"'string with a ; in it' string2\"", ret.stdout)
        self.assertIn("\"'file name with space.tex'\"", ret.stdout)
        self.assertIn("\"1\"", ret.stdout)
