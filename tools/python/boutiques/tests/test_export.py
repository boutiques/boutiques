#!/usr/bin/env python

import os
from unittest import TestCase
from boutiques import bosh
from boutiques import __file__ as bfile
from boutiques.exporter import ExportError

class TestImport(TestCase):
    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_export(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        example1_desc = os.path.join(example1_dir, "example1_docker.json")
        example1_desc_doi = os.path.join(example1_dir,
                                         "example1_docker_with_doi.json")
        fout = "test-example1-carmin.json"
        # Identifier is passed, descriptor has no DOI
        self.assertFalse(bosh(["export", "carmin", example1_desc, "--identifier", "123", fout]))
        # Identifier is not passed, descriptor has no DOI
       # self.assertRaises(ExportError, bosh(["export",
       #                                      "carmin",
       #                                      example1_desc,
       #                                      fout]))
        # Identifier is not passed, descriptor has no DOI
        self.assertFalse(bosh(["export", "carmin", example1_desc_doi, fout]))
        os.remove(fout)
