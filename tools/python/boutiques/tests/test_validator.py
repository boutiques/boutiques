#!/usr/bin/env python

# test_docker.py
# Created by Greg Kiar on 2017-03-26.
# Email: gkiar07@gmail.com
# Copyright (c) 2017. All rights reserved.

from unittest import TestCase
from boutiques.validator import validate_json, main
from boutiques import __file__
from jsonschema.exceptions import ValidationError
import os.path as op
import os


class TestSchema(TestCase):

    def test_runtime(self):
        fil = op.join(op.split(__file__)[0], 'schema/examples/good.json')
        self.assertFalse(main([fil]))

    def test_success(self):
        fil = op.join(op.split(__file__)[0], 'schema/examples/good.json')
        self.assertFalse(validate_json(fil))

    def test_fail(self):
        fil = op.join(op.split(__file__)[0], 'schema/examples/bad.json')
        self.assertRaises(ValidationError, validate_json, fil)

    def test_invalid(self):
        fil = op.join(op.split(__file__)[0], 'schema/examples/invalid.json')
        self.assertRaises(ValidationError, validate_json, fil)
