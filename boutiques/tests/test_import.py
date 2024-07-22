#!/usr/bin/env python

import os
import os.path as op
import subprocess
import tarfile
from os.path import join as opj

import pytest
import simplejson as json
from jsonschema.exceptions import ValidationError

import boutiques
from boutiques import bosh
from boutiques.importer import ImportError
from boutiques.tests.BaseTest import BaseTest
from boutiques.util.utils import loadJson


class TestImport(BaseTest):

    @pytest.fixture(scope='session', autouse=True)
    def clean_up(self):
        yield
        remove_list = ["user-image.simg", "example.conf", "stdout.txt"]
        for item in remove_list:
            if os.path.isfile(item):
                os.remove(item)

    def test_import_bids_good(self):
        self.setup("bids")
        bids_app = self.get_file_path("example_good")
        outfile = "./test_temp/test-import.json"
        ref_name = "test-import-ref.json"
        if op.isfile(outfile):
            os.remove(outfile)
        self.assertFalse(bosh(["import", "bids", outfile, bids_app]))
        self.assertEqual(open(outfile).read().strip(),
                         open(opj(bids_app, ref_name)).read().strip())
        self.assertFalse(bosh(["validate", outfile, "-b"]))

    def test_import_bids_bad(self):
        self.setup("bids")
        bids_app = self.get_file_path("example_bad")
        self.assertRaises(ValidationError, bosh, ["import", "bids",
                                                  "test-import.json",
                                                  bids_app])

    def test_upgrade_04(self):
        self.setup("import")
        fin = self.get_file_path("upgrade04.json")
        fout = self.get_file_path("upgrade05.json")
        ref_file = self.get_file_path("test-import-04-ref.json")
        ref_file_p2 = self.get_file_path("test-import-04-ref-python2.json")
        if op.isfile(fout):
            os.remove(fout)
        self.assertFalse(bosh(["import", "0.4",  fout, fin]))
        result = json.loads(open(fout).read().strip())
        self.assertIn(result,
                      [json.loads(open(ref_file).read().strip()),
                       json.loads(open(ref_file_p2).read().strip())])
        os.remove(fout)

    def test_upgrade_04_json_obj(self):
        self.setup("import")
        fin = open(self.get_file_path("upgrade04.json")).read()
        fout = self.get_file_path("upgrade05.json")
        ref_file = self.get_file_path("test-import-04-ref.json")
        ref_file_p2 = self.get_file_path("test-import-04-ref-python2.json")
        if op.isfile(fout):
            os.remove(fout)
        self.assertFalse(bosh(["import", "0.4",  fout, fin]))
        result = json.loads(open(fout).read().strip())
        self.assertIn(result,
                      [json.loads(open(ref_file).read().strip()),
                       json.loads(open(ref_file_p2).read().strip())])
        os.remove(fout)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_import_cwl_valid(self):
        self.setup("import/cwl/")
        ex_dir = self.get_file_path("")
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
            cwl_descriptor = op.abspath(opj(ex_dir, d, d+".cwl"))
            cwl_invocation = op.abspath(opj(ex_dir, d, d+".yml"))
            assert(os.path.isfile(cwl_descriptor))
            out_desc = "./test_temp/cwl_out.json"
            out_inv = "./test_temp/cwl_inv_out.json"
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
                    with open('./test_temp/hello.js', 'w') as f:
                        f.write("'hello'")
                    with open('./test_temp/goodbye.txt', 'w') as f:
                        f.write("goodbye")
                    # closing required for Python 2.6...
                    with tarfile.open('./test_temp/hello.tar',
                                      'w') as tar:
                        tar.add('./test_temp/goodbye.txt')
                    ret = boutiques.execute(
                            "launch",
                            out_desc,
                            out_inv,
                            "--skip-data-collection"
                          )
                    self.assertFalse(ret.exit_code,
                                     cwl_descriptor)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_docopt_import_valid(self):
        self.setup("import/docopt/")
        pydocopt_input = self.get_file_path("docopt_script_valid.py")
        output_descriptor = self.get_file_path("test_valid_output.json")

        import_args = ["import", "docopt", output_descriptor, pydocopt_input]
        bosh(import_args)

        test_invocation = self.get_file_path("valid_invoc_mutex.json")
        launch_args = ["exec", "launch", output_descriptor, test_invocation]
        bosh(launch_args)

        os.remove(output_descriptor)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_docopt_import_valid_options(self):
        self.setup("import/docopt/")
        pydocopt_input = self.get_file_path("docopt_script_options.py")
        output_descriptor = self.get_file_path("test_options_output.json")

        import_args = ["import", "docopt", output_descriptor, pydocopt_input]
        bosh(import_args)

        test_invocation = self.get_file_path("test_options_invocation.json")
        launch_args = ["exec", "launch", output_descriptor, test_invocation]
        bosh(launch_args)

        os.remove(output_descriptor)

    def test_docopt_import_invalid(self):
        self.setup("import/docopt/")
        pydocopt_input = self.get_file_path("docopt_script_invalid.py")
        output_descriptor = self.get_file_path("foobar.json")

        args = ["import", "docopt", output_descriptor, pydocopt_input]

        with pytest.raises(ImportError, match="Invalid docopt script"):
            bosh(args)
            self.fail("Did not raise ImportError or" +
                      " message did not match Invalid docopt script")

        if op.isfile(output_descriptor):
            self.fail("Output file should not exist")

    def test_docopt_nf(self):
        self.setup("import/docopt/")
        pydocopt_input = self.get_file_path("naval_fate.py")
        output_descriptor = self.get_file_path("naval_fate_descriptor.json")

        import_args = ["import", "docopt", output_descriptor, pydocopt_input]
        bosh(import_args)

        test_invocation = self.get_file_path("nf_invoc_new.json")
        launch_args = ["exec", "simulate", output_descriptor,
                       "-i", test_invocation]
        bosh(launch_args)

        test_invocation = self.get_file_path("nf_invoc_move.json")
        launch_args = ["exec", "simulate", output_descriptor,
                       "-i", test_invocation]
        bosh(launch_args)

        test_invocation = self.get_file_path("nf_invoc_shoot.json")
        launch_args = ["exec", "simulate", output_descriptor,
                       "-i", test_invocation]
        bosh(launch_args)

        test_invocation = self.get_file_path("nf_invoc_mine.json")
        launch_args = ["exec", "simulate", output_descriptor,
                       "-i", test_invocation]
        bosh(launch_args)

        test_invocation = self.get_file_path("nf_invoc_help.json")
        launch_args = ["exec", "simulate", output_descriptor,
                       "-i", test_invocation]
        bosh(launch_args)

        os.remove(output_descriptor)

    def test_import_json_config(self):
        self.setup("import/config/")
        expected_desc = loadJson(self.get_file_path("json_config_desc.json"))
        config = self.get_file_path("configuration.json")
        output_descriptor = self.get_file_path("output.json")

        import_args = ["import", "config", output_descriptor, config]
        bosh(import_args)
        result_desc = loadJson(output_descriptor)

        if op.exists(output_descriptor):
            os.remove(output_descriptor)
        self.assertEqual(expected_desc, result_desc)

        # Groups are needed in template but causes tests to fail
        del result_desc['groups']
        # Tests the generated descriptor by running it with a test invocation
        test_invoc = self.get_file_path("test_config_import_invoc.json")
        simulate_args = ["exec", "simulate", json.dumps(result_desc),
                         "-i", test_invoc]

        expected_cml = ("tool config.json")
        result_cml = bosh(simulate_args).shell_command

        with open(self.get_file_path("expected_config.json"), "r") as c:
            expect_sim_out = c.readlines()
        if op.exists(result_desc['output-files'][0]['path-template']):
            with open(result_desc['output-files']
                      [0]['path-template'], "r") as r:
                result_sim_out = r.readlines()
            os.remove(result_desc['output-files'][0]['path-template'])

        # Validate by comparing generated command-line output
        # Validate by comparing generated simulated config file
        self.assertEqual(result_cml, expected_cml)
        self.assertEqual(result_sim_out, expect_sim_out)

    def test_import_toml_config(self):
        self.setup("import/config/")
        expected_desc = loadJson(self.get_file_path("toml_config_desc.json"))
        config = self.get_file_path("configuration.toml")
        output_descriptor = self.get_file_path("output.json")

        import_args = ["import", "config", output_descriptor, config]
        bosh(import_args)
        result_desc = loadJson(output_descriptor)

        if op.exists(output_descriptor):
            os.remove(output_descriptor)
        self.assertEqual(expected_desc, result_desc)

        # Groups are needed in template but causes tests to fail
        del result_desc['groups']
        # Tests the generated descriptor by running it with a test invocation
        test_invoc = self.get_file_path("test_config_import_invoc.json")
        simulate_args = ["exec", "simulate", json.dumps(result_desc),
                         "-i", test_invoc]

        expected_cml = ("tool config.toml")
        result_cml = bosh(simulate_args).shell_command

        with open(self.get_file_path("expected_config.toml"), "r") as c:
            expect_sim_out = c.readlines()
        if op.exists(result_desc['output-files'][0]['path-template']):
            with open(result_desc['output-files']
                      [0]['path-template'], "r") as r:
                result_sim_out = r.readlines()
            os.remove(result_desc['output-files'][0]['path-template'])

        # Validate by comparing generated command-line output
        # Validate by comparing generated simulated config file
        self.assertEqual(result_cml, expected_cml)
        self.assertEqual(result_sim_out, expect_sim_out)

    def test_import_yaml_config(self):
        self.setup("import/config/")
        expected_desc = loadJson(self.get_file_path("yaml_config_desc.json"))
        config = self.get_file_path("configuration.yml")
        output_descriptor = self.get_file_path("output.json")

        import_args = ["import", "config", output_descriptor, config]
        bosh(import_args)
        result_desc = loadJson(output_descriptor)

        if op.exists(output_descriptor):
            os.remove(output_descriptor)
        self.assertEqual(expected_desc, result_desc)

        # Groups are needed in template but causes tests to fail
        del result_desc['groups']
        # Tests the generated descriptor by running it with a test invocation
        test_invoc = self.get_file_path("test_config_import_invoc.json")
        simulate_args = ["exec", "simulate", json.dumps(result_desc),
                         "-i", test_invoc]

        expected_cml = ("tool config.yml")
        result_cml = bosh(simulate_args).shell_command

        with open(self.get_file_path("expected_config.yml"), "r") as c:
            expect_sim_out = c.readlines()
        if op.exists(result_desc['output-files'][0]['path-template']):
            with open(result_desc['output-files']
                      [0]['path-template'], "r") as r:
                result_sim_out = r.readlines()
            os.remove(result_desc['output-files'][0]['path-template'])

        # Validate by comparing generated command-line output
        # Validate by comparing generated simulated config file
        self.assertEqual(result_cml, expected_cml)
        self.assertEqual(result_sim_out, expect_sim_out)
