#!/usr/bin/env python

from unittest import TestCase
from boutiques.validator import validate_json, main as main_validate
from boutiques.importer import main
from boutiques.bids import validate_bids
from boutiques import __file__ as bofile
from jsonschema.exceptions import ValidationError
import os.path as op
import json
import os


class TestImport(TestCase):

    def test_import_bids_good(self):
        bids_app = op.join(op.split(bofile)[0], "schema/examples/bids-apps/example_good")
        self.assertFalse(main(args=["bids",
                                    "--bids_app_dir", bids_app,
                                    "test-import.json"]))

    def test_import_bids_bad(self):
        bids_app = op.join(op.split(bofile)[0], "schema/examples/bids-apps/example_bad")
        self.assertRaises(ValidationError, main, ["bids",
                                                  "--bids_app_dir", bids_app,
                                                  "test-import.json"])

    def test_import_bids_valid(self):
        self.assertFalse(main_validate(args=["-b","test-import.json"]))
        os.remove("test-import.json")

    def test_upgrade_04(self):
        fin = op.join(op.split(bofile)[0], "schema/examples/upgrade04.json")
        fout = op.join(op.split(bofile)[0], "schema/examples/upgraded05.json")
        self.assertFalse(main(args=["0.4",  fout,
                                    "--input_file", fin]))
        os.remove(fout)
        
