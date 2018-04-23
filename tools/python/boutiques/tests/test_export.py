#!/usr/bin/env python

import os
from os.path import join as opj
from unittest import TestCase
from boutiques import bosh
from boutiques import __file__ as bfile


class TestImport(TestCase):
    def get_examples_dir(self):
        return opj(os.path.dirname(bfile),
                   "schema", "examples")

    def test_export(self):
        example1_dir = opj(self.get_examples_dir(), "example1")
        example1_desc = opj(example1_dir, "example1_docker.json")
        fout = "test-example1-carmin.json"
        bosh(["export", "carmin", example1_desc, "123", fout])
        ref_name = "example1_docker_exported.json"
        assert(open(fout, "r").read().strip() == open(opj(example1_dir,
                                                          ref_name),
                                                      "r").read().strip())
        os.remove(fout)
