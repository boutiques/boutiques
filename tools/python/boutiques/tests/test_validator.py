#!/usr/bin/env python

from unittest import TestCase
from boutiques.bosh import bosh
from boutiques import __file__ as bfile
from boutiques.validator import DescriptorValidationError
import os.path as op
import os


class TestValidator(TestCase):

    def test_runtime(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/good.json')
        self.assertFalse(bosh(['validate', fil]))

    def test_success(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/good.json')
        assert bosh(['validate', fil]) is not None

    def test_fail(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/bad.json')
        self.assertRaises(DescriptorValidationError, bosh, ['validate', fil])

    def test_invalid(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/invalid.json')
        self.assertRaises(DescriptorValidationError, bosh, ['validate', fil])
