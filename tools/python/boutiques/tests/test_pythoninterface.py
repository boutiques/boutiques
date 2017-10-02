#!/usr/bin/env python

import os, os.path as op, subprocess
from unittest import TestCase
from boutiques import __file__ as bfile
from boutiques.bosh import BoutiquesTools

class TestBoutiquesTools(TestCase):

    def test_pythoninterface_validate(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/good.json')
        bosh = BoutiquesTools()
        assert bosh.validate(fil) is not None

