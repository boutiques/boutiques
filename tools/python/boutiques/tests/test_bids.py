#!/usr/bin/env python

from unittest import TestCase
from boutiques.bosh import bosh
from boutiques.bids import validate_bids
from boutiques import __file__ as bofile
from jsonschema.exceptions import ValidationError
import os.path as op
import json
import os


class TestBIDS(TestCase):

    def test_bids_good(self):
        fil = op.join(op.split(bofile)[0], 'schema/examples/bids_good.json')
        self.assertFalse(bosh(["validate", fil, '-b']))

    def test_bids_bad1(self):
        fil = op.join(op.split(bofile)[0], 'schema/examples/bids_bad1.json')
        self.assertRaises(ValidationError, bosh, ["validate", fil, '-b'])

    def test_bids_bad2(self):
        fil = op.join(op.split(bofile)[0], 'schema/examples/bids_bad2.json')
        self.assertRaises(ValidationError, bosh, ["validate", fil, '-b'])

    def test_bids_invalid(self):
        fil = op.join(op.split(bofile)[0], 'schema/examples/bids_bad2.json')
        descriptor = json.load(open(fil))
        self.assertRaises(ValidationError, validate_bids, descriptor, False)
