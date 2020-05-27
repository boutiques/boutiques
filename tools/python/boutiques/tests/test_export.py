#!/usr/bin/env python

import os
import sys
from unittest import TestCase
from boutiques import bosh
from boutiques import __file__ as bfile
from boutiques.exporter import ExportError
from os.path import join as opj
from unittest import TestCase


class TestExport(TestCase):
    def get_examples_dir(self):
        return opj(os.path.dirname(bfile),
                   "schema", "examples")

    def test_export(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        example1_desc = os.path.join(example1_dir, "example1_docker.json")
        example1_desc_doi = os.path.join(example1_dir,
                                         "example1_docker_with_doi.json")
        fout = "test-example1-carmin.json"
        ref_name = "example1_docker_exported.json"
        ref_file = opj(example1_dir, ref_name)
        ref_name_p2 = "example1_docker_exported_python2.json"
        ref_file_p2 = opj(example1_dir, ref_name_p2)
        # Identifier is passed, descriptor has no DOI
        self.assertFalse(bosh(["export",
                               "carmin",
                               example1_desc,
                               "--identifier", "123", fout]))
        result = open(fout).read().strip()
        assert(result == open(ref_file).read().strip() or
               result == open(ref_file_p2).read().strip())
        # Identifier is not passed, descriptor has no DOI
        with self.assertRaises(ExportError) as e:
            bosh(["export",
                  "carmin",
                  example1_desc,
                  fout])
        self.assertTrue("Descriptor must have a DOI, or identifier "
                        "must be specified" in str(e.exception))
        self.assertRaises(ExportError, )
        # Identifier is not passed, descriptor has a DOI
        ref_name = "example1_docker_exported_doi.json"
        ref_file = opj(example1_dir, ref_name)
        ref_name_p2 = "example1_docker_exported_doi_python2.json"
        ref_file_p2 = opj(example1_dir, ref_name_p2)
        self.assertFalse(bosh(["export", "carmin", example1_desc_doi, fout]))
        result = open(fout).read().strip()
        self.assertIn(result, [open(ref_file).read().strip(),
                               open(ref_file_p2).read().strip()])
        os.remove(fout)

    def test_export_json_obj(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        example1_desc = open(os.path.join(example1_dir,
                             "example1_docker.json")).read()
        example1_desc_doi = os.path.join(example1_dir,
                                         "example1_docker_with_doi.json")
        fout = "test-example1-carmin.json"
        ref_name = "example1_docker_exported.json"
        ref_file = opj(example1_dir, ref_name)
        ref_name_p2 = "example1_docker_exported_python2.json"
        ref_file_p2 = opj(example1_dir, ref_name_p2)
        # Identifier is passed, descriptor has no DOI
        self.assertFalse(bosh(["export",
                               "carmin",
                               example1_desc,
                               "--identifier", "123", fout]))
        result = open(fout).read().strip()
        self.assertIn(result, [open(ref_file).read().strip(),
                               open(ref_file_p2).read().strip()])
        # Identifier is not passed, descriptor has no DOI
        with self.assertRaises(ExportError) as e:
            bosh(["export",
                  "carmin",
                  example1_desc,
                  fout])
        self.assertIn("Descriptor must have a DOI, or identifier "
                      "must be specified", str(e.exception))
        self.assertRaises(ExportError, )
        # Identifier is not passed, descriptor has a DOI
        ref_name = "example1_docker_exported_doi.json"
        ref_file = opj(example1_dir, ref_name)
        ref_name_p2 = "example1_docker_exported_doi_python2.json"
        ref_file_p2 = opj(example1_dir, ref_name_p2)
        self.assertFalse(bosh(["export", "carmin", example1_desc_doi, fout]))
        result = open(fout).read().strip()
        self.assertIn(result, [open(ref_file).read().strip(),
                               open(ref_file_p2).read().strip()])
        os.remove(fout)
