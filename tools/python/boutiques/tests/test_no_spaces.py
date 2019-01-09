#!/usr/bin/env python

import os
import subprocess
import pytest
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh


class TestNoSpaces(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_no_spaces(self):
        out = bosh.execute("simulate",
                           os.path.join(self.get_examples_dir(),
                                        "no_spaces.json"))
        assert(' ' not in out.stdout)
