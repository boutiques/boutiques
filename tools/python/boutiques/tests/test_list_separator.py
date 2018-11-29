#!/usr/bin/env python

import os
import subprocess
import pytest
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh


class TestListSeparator(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_list_separator(self):
        out = bosh.execute("simulate",
                           os.path.join(self.get_examples_dir(),
                                        "list_separator.json"),
                           "-i",
                           os.path.join(self.get_examples_dir(),
                                        "list_separator_inv.json"))
        assert('1:2:3' in out.stdout)
