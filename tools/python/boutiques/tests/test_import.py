#!/usr/bin/env python

from unittest import TestCase
from boutiques import bosh
from boutiques import __file__ as bfile
from jsonschema.exceptions import ValidationError
import os
import os.path as op
from os.path import join as opj
import pytest
from boutiques.importer import ImportError
import boutiques
import tarfile
from contextlib import closing
import simplejson as json


class TestImport(TestCase):

    def test_import_bids_good(self):
        bids_app = opj(op.split(bfile)[0],
                       "schema/examples/bids-apps/example_good")
        outfile = "test-import.json"
        ref_name = "test-import-ref.json"
        if op.isfile(outfile):
            os.remove(outfile)
        self.assertFalse(bosh(["import", "bids", outfile, bids_app]))
        self.assertEqual(open(outfile, "U").read().strip(),
                         open(opj(bids_app, ref_name),
                              "U").read().strip())

    def test_import_bids_bad(self):
        bids_app = opj(op.split(bfile)[0],
                       "schema/examples/bids-apps/example_bad")
        self.assertRaises(ValidationError, bosh, ["import", "bids",
                                                  "test-import.json",
                                                  bids_app])

    def test_import_bids_valid(self):
        self.assertFalse(bosh(["validate", "test-import.json", "-b"]))
        os.remove("test-import.json")

    def test_upgrade_04(self):
        fin = opj(op.split(bfile)[0], "schema/examples/upgrade04.json")
        fout = opj(op.split(bfile)[0], "schema/examples/upgraded05.json")
        ref_name = "test-import-04-ref.json"
        ref_file = opj(op.split(bfile)[0], "schema/examples", ref_name)
        ref_name_p2 = "test-import-04-ref-python2.json"
        ref_file_p2 = opj(op.split(bfile)[0], "schema/examples",
                          ref_name_p2)
        if op.isfile(fout):
            os.remove(fout)
        self.assertFalse(bosh(["import", "0.4",  fout, fin]))
        result = open(fout, "U").read().strip()
        self.assertIn(result, [open(ref_file, "U").read().strip(),
                               open(ref_file_p2, "U").read().strip()])
        os.remove(fout)

    def test_upgrade_04_json_obj(self):
        fin = open(opj(op.split(bfile)[0],
                   "schema/examples/upgrade04.json")).read()
        fout = opj(op.split(bfile)[0], "schema/examples/upgraded05.json")
        ref_name = "test-import-04-ref.json"
        ref_file = opj(op.split(bfile)[0], "schema/examples", ref_name)
        ref_name_p2 = "test-import-04-ref-python2.json"
        ref_file_p2 = opj(op.split(bfile)[0], "schema/examples",
                          ref_name_p2)
        if op.isfile(fout):
            os.remove(fout)
        self.assertFalse(bosh(["import", "0.4",  fout, fin]))
        result = open(fout, "U").read().strip()
        self.assertIn(result, [open(ref_file, "U").read().strip(),
                               open(ref_file_p2, "U").read().strip()])
        os.remove(fout)

    def test_import_cwl_valid(self):
        ex_dir = opj(op.split(bfile)[0], "tests/cwl")
        # These ones are supposed to crash
        bad_dirs = ["1st-workflow",  # workflow
                    "record",  # complex type
                    "array-inputs",  # input bindings specific to array element
                    "expression",  # Javascript expression
                    "nestedworkflows"  # workflow
                    ]
        for d in os.listdir(ex_dir):
            if d == "README.md":
                continue
            files = os.listdir(opj(ex_dir, d))
            cwl_descriptor = op.abspath(opj(ex_dir, d, d+".cwl"))
            cwl_invocation = op.abspath(opj(ex_dir, d, d+".yml"))
            assert(os.path.isfile(cwl_descriptor))
            out_desc = "./cwl_out.json"
            out_inv = "./cwl_inv_out.json"
            run = False
            if os.path.isfile(cwl_invocation):
                args = ["import",
                        "cwl",
                        out_desc,
                        cwl_descriptor,
                        "-i", cwl_invocation,
                        "-o", out_inv]
                run = True
            else:
                args = ["import",
                        "cwl",
                        out_desc,
                        cwl_descriptor]
            if d in bad_dirs:
                with pytest.raises(ImportError):
                    bosh(args)
            else:
                self.assertFalse(bosh(args), cwl_descriptor)
                if run:
                    # write files required by cwl tools
                    with open('hello.js', 'w') as f:
                        f.write("'hello'")
                    with open('goodbye.txt', 'w') as f:
                        f.write("goodbye")
                    # closing required for Python 2.6...
                    with tarfile.open('hello.tar',
                                      'w') as tar:
                        tar.add('goodbye.txt')
                    ret = boutiques.execute(
                            "launch",
                            out_desc,
                            out_inv,
                            "--skip-data-collection"
                          )
                    self.assertFalse(ret.exit_code,
                                     cwl_descriptor)

    def test_import_docopt_valid(self):
        base_path = op.join(op.split(bfile)[0], "tests/docopt")
        pydocopt_input = op.join(base_path, "test_valid.py")
        descriptor_output = op.join(base_path, "test_valid_output.json")
        expected_output = op.join(base_path, "test_valid.json")

        args = ["import", "dcpt", descriptor_output, pydocopt_input]
        if op.isfile(descriptor_output):
            os.remove(descriptor_output)
        bosh(args)
        result = json.loads(
            open(descriptor_output, "r").read().strip())
        expected = json.loads(
            open(expected_output, "r").read().strip())
        os.remove(descriptor_output)

        self.assertEqual(expected['command-line'], result['command-line'])

        for result_input in result['groups']:
            self.assertIn(result_input, expected['groups'])

        for result_input in result['inputs']:
            self.assertIn(result_input, expected['inputs'])

    def test_import_docopt_valid_options(self):
        base_path = op.join(op.split(bfile)[0], "tests/docopt")
        pydocopt_input = op.join(base_path, "test_options.py")
        descriptor_output = op.join(base_path, "test_options_output.json")
        expected_output = op.join(base_path, "test_options.json")

        args = ["import", "dcpt", descriptor_output, pydocopt_input]
        if op.isfile(descriptor_output):
            os.remove(descriptor_output)
        bosh(args)
        result = json.loads(
            open(descriptor_output, "r").read().strip())
        expected = json.loads(
            open(expected_output, "r").read().strip())
        os.remove(descriptor_output)

        self.assertEqual(expected['command-line'], result['command-line'])

        for result_input in result['inputs']:
            self.assertIn(result_input, expected['inputs'])

    def test_import_docopt_invalid(self):
        base_path = op.join(op.split(bfile)[0], "tests/docopt")
        pydocopt_input = op.join(base_path, "test_invalid.py")
        descriptor_output = op.join(base_path, "foobar.json")

        args = ["import", "dcpt", descriptor_output, pydocopt_input]

        with pytest.raises(ImportError, match="Invalid docopt script"):
            bosh(args)
            self.fail("Did not raise ImportError or" +
                      " message did not match Invalid docopt script")

        if op.isfile(descriptor_output):
            self.fail("Output file should not exist")
