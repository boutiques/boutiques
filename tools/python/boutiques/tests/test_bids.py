#!/usr/bin/env python

from unittest import TestCase
from boutiques.validator import validate_json, main
from boutiques.bids import validate_bids
from boutiques import __file__
from jsonschema.exceptions import ValidationError
import os.path as op
import json
import os


class TestBIDS(TestCase):

    def test_bids_good(self):
        fil = op.join(op.split(__file__)[0], 'schema/examples/bids_good.json')
        self.assertFalse(main(args=[fil, '-b']))

    def test_bids_bad1(self):
        fil = op.join(op.split(__file__)[0], 'schema/examples/bids_bad1.json')
        self.assertRaises(ValidationError, main, [fil, '-b'])

    def test_bids_bad2(self):
        fil = op.join(op.split(__file__)[0], 'schema/examples/bids_bad2.json')
        self.assertRaises(ValidationError, main, [fil, '-b'])

    def test_bids_invalid(self):
        fil = op.join(op.split(__file__)[0], 'schema/examples/bids_bad2.json')
        descriptor = json.load(open(fil))
        self.assertRaises(ValidationError, validate_bids, descriptor, False)
