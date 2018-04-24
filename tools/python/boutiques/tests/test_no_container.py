#!/usr/bin/env python

import os
import subprocess
import pytest
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh


class TestExample1(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_no_container(self):
        self.assertFalse(bosh.execute("launch",
                                      os.path.join(self.get_examples_dir(),
                                                   "no_container.json"),
                                      os.path.join(self.get_examples_dir(),
                                                   "no_container_invocation."
                                                   + "json")).exit_code)
