#!/usr/bin/env python

from unittest import TestCase
from boutiques import bosh
from boutiques import __file__ as bfile
from jsonschema.exceptions import ValidationError
import json
import os
import os.path as op
from os.path import join as opj


class TestImport(TestCase):

    def test_import_bids_good(self):
        bids_app = op.join(op.split(bfile)[0],
                           "schema/examples/bids-apps/example_good")
        outfile = "test-import.json"
        ref_name = "test-import-ref.json"
        if op.isfile(outfile):
                os.remove(outfile)
        self.assertFalse(bosh(["import", "bids", outfile, bids_app]))
        assert(open(outfile, "r").read().strip() == open(opj(bids_app,
                                                             ref_name),
                                                         "r").read().strip())

    def test_import_bids_bad(self):
        bids_app = op.join(op.split(bfile)[0],
                           "schema/examples/bids-apps/example_bad")
        self.assertRaises(ValidationError, bosh, ["import", "bids",
                                                  "test-import.json",
                                                  bids_app])

    def test_import_bids_valid(self):
        self.assertFalse(bosh(["validate", "test-import.json", "-b"]))
        os.remove("test-import.json")

    def test_upgrade_04(self):
        fin = op.join(op.split(bfile)[0], "schema/examples/upgrade04.json")
        fout = op.join(op.split(bfile)[0], "schema/examples/upgraded05.json")
        ref_name = "test-import-04-ref.json"
        if op.isfile(fout):
                os.remove(fout)
        self.assertFalse(bosh(["import", "0.4",  fout, fin]))
        assert(open(fout, "r").read().strip() == open(opj("schema/examples",
                                                          ref_name),
                                                      "r").read().strip())
        os.remove(fout)
