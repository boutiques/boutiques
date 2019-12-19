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
        prettystring = bosh.pprint(fil)
        self.assertIsInstance(prettystring, string_types)

    def test_categories_and_order(self):
        fil = op.join(op.split(bfile)[0],
                      'schema/examples/test_pretty_print.json')
        prettystring = bosh.pprint(fil)
        i_tl_descs = prettystring.index("Tool name")
        i_con_info = prettystring.index("Container Information")
        i_sugg_res = prettystring.index("Suggested Resources")
        i_er_codes = prettystring.index("Error Codes")
        i_inp_grps = prettystring.index("Input Groups")
        i_pos_args = prettystring.index("positional arguments")
        i_opt_args = prettystring.index("optional arguments")
        i_req_args = prettystring.index("required arguments")
        i_conf_fil = prettystring.index("Config Files")
        i_out_file = prettystring.index("Output Files")

        # Fluff asserts for easy debugging
        self.assertTrue(i_tl_descs < i_con_info)
        self.assertTrue(i_con_info < i_sugg_res)
        self.assertTrue(i_sugg_res < i_er_codes)
        self.assertTrue(i_er_codes < i_inp_grps)
        self.assertTrue(i_inp_grps < i_pos_args)
        self.assertTrue(i_pos_args < i_opt_args)
        self.assertTrue(i_opt_args < i_req_args)
        self.assertTrue(i_req_args < i_conf_fil)
        self.assertTrue(i_conf_fil < i_out_file)

    def test_input_optionality_separation(self):
        fil = op.join(op.split(bfile)[0],
                      'schema/examples/test_pretty_print.json')
        prettystring = bosh.pprint(fil)
        inputs = prettystring.split("=" * 80)[6].split("arguments:")
        positional_inputs = inputs[1]
        optional_inputs = inputs[2]
        required_inputs = inputs[3]
        self.assertFalse("Optional: False" in positional_inputs)
        self.assertFalse("Optional: False" in optional_inputs)
        self.assertFalse("Optional: True" in required_inputs)

    def test_output_config_separation(self):
        self.maxDiff = None
        fil = op.join(op.split(bfile)[0],
                      'schema/examples/test_pretty_print.json')
        prettystring = bosh.pprint(fil)
        categories = prettystring.split("=" * 80)
        configs = categories[7]
        outputs = categories[8]
        self.assertTrue("Config Files:" in configs)
        self.assertTrue("Template:" in configs)
        self.assertTrue("Output Files:" in outputs)
        self.assertFalse("Template:" in outputs)

    def test_duplcate_flags(self):
        fil = op.join(op.split(bfile)[0],
                      'schema/examples/good_dupFlags.json')
        prettystring = bosh.prettyprint(fil)
        self.assertIn("-duplicate", prettystring)
        self.assertIn("-duplicate_DUP1", prettystring)
        self.assertIn("-duplicate_DUP2", prettystring)
