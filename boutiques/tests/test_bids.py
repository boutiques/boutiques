#!/usr/bin/env python

import pytest

from boutiques.bids import validate_bids
from boutiques.bosh import bosh
from boutiques.tests.BaseTest import BaseTest
from boutiques.validator import DescriptorValidationError


class TestBIDS(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("bids")

    def test_bids_good(self):
        fil = self.get_file_path("bids_good.json")
        self.assertFalse(bosh(["validate", fil, "-b"]))

    def test_bids_bad1(self):
        fil = self.get_file_path("bids_bad1.json")
        self.assertRaises(DescriptorValidationError, bosh, ["validate", fil, "-b"])

    def test_bids_bad2(self):
        fil = self.get_file_path("bids_bad2.json")
        self.assertRaises(DescriptorValidationError, bosh, ["validate", fil, "-b"])

    def test_bids_invalid(self):
        import simplejson as json

        fil = self.get_file_path("bids_bad2.json")
        descriptor = json.load(open(fil))
        self.assertRaises(DescriptorValidationError, validate_bids, descriptor, False)
