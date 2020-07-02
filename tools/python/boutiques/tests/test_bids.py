#!/usr/bin/env python

from boutiques.bosh import bosh
from boutiques.bids import validate_bids
from jsonschema.exceptions import ValidationError
from boutiques.validator import DescriptorValidationError
from boutiques.util.BaseTest import BaseTest
import os.path as op
import simplejson as json


class TestBIDS(BaseTest):

    def test_bids_good(self):
        fil = op.join(self.schema_examples_dir, 'bids', 'bids_good.json')
        self.assertFalse(bosh(["validate", fil, '-b']))

    def test_bids_bad1(self):
        fil = op.join(self.schema_examples_dir, 'bids', 'bids_bad1.json')
        self.assertRaises(DescriptorValidationError, bosh, ["validate",
                                                            fil, '-b'])

    def test_bids_bad2(self):
        fil = op.join(self.schema_examples_dir, 'bids', 'bids_bad2.json')
        self.assertRaises(DescriptorValidationError, bosh, ["validate",
                                                            fil, '-b'])

    def test_bids_invalid(self):
        fil = op.join(self.schema_examples_dir, 'bids', 'bids_bad2.json')
        descriptor = json.load(open(fil))
        self.assertRaises(DescriptorValidationError, validate_bids,
                          descriptor, False)
