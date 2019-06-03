#!/usr/bin/env python

import os
import os.path as op
from unittest import TestCase
from boutiques import __file__ as bfile
from six import string_types
import boutiques as bosh


class TestPPrint(TestCase):

    def test_doesntcrash(self):
        fil = op.join(op.split(bfile)[0],
                      'schema/examples/test_pretty_print.json')
        prettystring = bosh.prettyprint(fil)
        self.assertIsInstance(prettystring, string_types)
