#!/usr/bin/env python

import os
from unittest import TestCase
from boutiques import bosh
from boutiques import __file__ as bfile


class TestImport(TestCase):
    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_export(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        example1_desc = os.path.join(example1_dir, "example1_docker.json")
        fout = "test-example1-carmin.json"
        self.assertFalse(bosh(["export", "carmin", example1_desc, "123", fout]))
        os.remove(fout)
