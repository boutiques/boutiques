#!/usr/bin/env python

import os, os.path as op, subprocess
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques

class TestBoutiquesTools(TestCase):

    def test_pythoninterface_validate(self):
        fil = op.join(op.split(bfile)[0], 'schema/examples/good.json')
        assert boutiques.validate(fil) is not None

