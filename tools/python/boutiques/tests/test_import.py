#!/usr/bin/env python

from unittest import TestCase
from boutiques.bosh import bosh
from boutiques import __file__ as bfile
from jsonschema.exceptions import ValidationError
import os.path as op
import json
import os


class TestImport(TestCase):

    def test_import_bids_good(self):
        bids_app = op.join(op.split(bfile)[0], "schema/examples/bids-apps/example_good")
        self.assertFalse(bosh(["import", "bids",
                               "--bids_app", bids_app,
                               "test-import.json"]))

    def test_import_bids_bad(self):
        bids_app = op.join(op.split(bfile)[0], "schema/examples/bids-apps/example_bad")
        self.assertRaises(ValidationError, bosh, ["import", "bids",
                                                  "--bids_app", bids_app,
                                                  "test-import.json"])

    def test_import_bids_valid(self):
        self.assertFalse(bosh(["validate", "test-import.json", "-b"]))
        os.remove("test-import.json")

    def test_upgrade_04(self):
        fin = op.join(op.split(bfile)[0], "schema/examples/upgrade04.json")
        fout = op.join(op.split(bfile)[0], "schema/examples/upgraded05.json")
        self.assertFalse(bosh(["import", "0.4",  fout, "--input", fin]))
        os.remove(fout)

