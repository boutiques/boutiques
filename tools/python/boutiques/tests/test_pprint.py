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

    def test_order(self):
        fil = op.join(op.split(bfile)[0],
                      'schema/examples/test_pretty_print.json')
        prettystring = bosh.prettyprint(fil)
        i_pos_args = prettystring.index("positional arguments")
        i_opt_args = prettystring.index("optional arguments")
        i_req_args = prettystring.index("required arguments")
        i_conf_fil = prettystring.index("Config Files")
        i_out_fil = prettystring.index("Output Files")
        self.assertTrue(i_pos_args < i_opt_args)
        self.assertTrue(i_opt_args < i_req_args)
        self.assertTrue(i_req_args < i_conf_fil)
        self.assertTrue(i_conf_fil < i_out_fil)
