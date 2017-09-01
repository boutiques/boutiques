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

    def test_import_good(self):
        bids_app = op.join(op.split(bofile)[0], 'schema/examples/bids-apps/example')
        self.assertFalse(main(args=[bids_app, 'test-import.json']))

    def test_import_valid(self):
        self.assertFalse(main_validate(args=['-b','test-import.json']))
        os.remove('test-import.json')
