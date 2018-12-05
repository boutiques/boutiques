#!/usr/bin/env python

import os, os.path as op
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh


class TestPPrint(TestCase):

    def test_doesntcrash(self):
        fil = op.join(op.split(bfile)[0],
                      'schema/examples/test_pretty_print.json')
        prettystring = bosh.prettyprint(fil)
        assert(isinstance(prettystring, str))
