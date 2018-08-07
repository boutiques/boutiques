#!/usr/bin/env python

from unittest import TestCase
from boutiques import bosh
from boutiques import __file__ as bfile
from jsonschema.exceptions import ValidationError
import json
import os
import os.path as op
from os.path import join as opj
import pytest
from boutiques.importer import ImportError


class TestImport(TestCase):

    def test_import_bids_good(self):
        bids_app = opj(op.split(bfile)[0],
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
        bids_app = opj(op.split(bfile)[0],
                       "schema/examples/bids-apps/example_bad")
        self.assertRaises(ValidationError, bosh, ["import", "bids",
                                                  "test-import.json",
                                                  bids_app])

    def test_import_bids_valid(self):
        self.assertFalse(bosh(["validate", "test-import.json", "-b"]))
        os.remove("test-import.json")

    def test_upgrade_04(self):
        fin = opj(op.split(bfile)[0], "schema/examples/upgrade04.json")
        fout = opj(op.split(bfile)[0], "schema/examples/upgraded05.json")
        ref_name = "test-import-04-ref.json"
        ref_file = opj(op.split(bfile)[0], "schema/examples", ref_name)
        ref_name_p2 = "test-import-04-ref-python2.json"
        ref_file_p2 = opj(op.split(bfile)[0], "schema/examples",
                          ref_name_p2)
        if op.isfile(fout):
                os.remove(fout)
        self.assertFalse(bosh(["import", "0.4",  fout, fin]))
        result = open(fout, "r").read().strip()
        assert(result == open(ref_file, "r").read().strip() or
               result == open(ref_file_p2, "r").read().strip())
        os.remove(fout)

    def test_import_cwl(self):
        ex_dir = opj(op.split(bfile)[0], "tests/cwl")
        # These ones are supposed to crash
        bad_dirs = ["1st-workflow", "record", "array-inputs",
                    "createfile", "expression", "nestedworkflows",
                    "arguments"]
        for d in os.listdir(ex_dir):
                if d == "README.md":
                        continue
                files = os.listdir(opj(ex_dir, d))
                cwl_descriptor = None
                cwl_invocation = None
                for f in files:
                        if op.basename(f).endswith(".cwl"):
                                cwl_descriptor = op.abspath(opj(ex_dir, d, f))
                        if op.basename(f).endswith(".yml"):
                                cwl_invocation = op.abspath(opj(ex_dir, d, f))
                assert(cwl_descriptor is not None)
                print(d)  # to help with debugging
                out_desc = "./cwl_out.json"
                out_inv = "./cwl_inv_out.json"
                if cwl_invocation is not None:
                        args = ["import",
                                "cwl",
                                out_desc,
                                cwl_descriptor,
                                "-i", cwl_invocation,
                                "-o", out_inv]
                else:
                        args = ["import",
                                "cwl",
                                out_desc,
                                cwl_descriptor]
                if d in bad_dirs:
                        with pytest.raises(ImportError):
                                bosh(args)
                else:
                        self.assertFalse(bosh(args))
