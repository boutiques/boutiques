#!/usr/bin/env python

import os
import re
import subprocess
import simplejson as json
from boutiques import __file__ as bfile
import boutiques as bosh
import mock
from boutiques.localExec import ExecutorError
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord,\
    example_boutiques_tool, mock_get
from boutiques.tests.BaseTest import BaseTest
import pytest


class TestSimulate(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("simulate")

    def test_success(self):
        self.assertFalse(
            bosh.execute("simulate", self.example1_descriptor).exit_code)

        self.assertFalse(
            bosh.execute("simulate", self.example1_descriptor,
                         self.get_file_path("good_nooutputs.json")).exit_code)

    def test_success_desc_as_json_obj(self):
        desc_json = open(self.example1_descriptor).read()
        self.assertFalse(
            bosh.execute("simulate", desc_json).exit_code)

    @mock.patch('requests.get', return_value=mock_get())
    def test_success_desc_from_zenodo(self, mock_get):
        self.assertFalse(
            bosh.execute("simulate",
                         "zenodo." + str(example_boutiques_tool.id)).exit_code)

    def test_success_default_values(self):
        self.assertFalse(
            bosh.execute("simulate",
                         self.example1_descriptor,
                         "-i",
                         self.get_file_path("inv_no_defaults.json")).exit_code)

    @mock.patch('random.uniform')
    def test_number_bounds(self, mock_random):
        desc_json = open(self.example1_descriptor).read()
        test_json = json.loads(desc_json)
        del test_json['groups']
        # Have to tweak flag_input because it disables number_input
        target_input = [i for i in test_json["inputs"]
                        if i["id"] == "flag_input"][0]
        del target_input["disables-inputs"]

        # Make number_input mandatory
        target_input = [i for i in test_json["inputs"]
                        if i["id"] == "num_input"][0]
        target_input["optional"] = False
        target_input["exclusive-minimum"] = False

        # Test inclusive lower bound
        mock_random.return_value = -0.001
        self.assertRaises(ExecutorError, bosh.execute, ("simulate",
                                                        json.dumps(test_json),
                                                        "-j"))
        mock_random.return_value = 0
        ret = bosh.bosh(args=["example", json.dumps(test_json)])
        self.assertIsInstance(json.loads(ret), dict)

        # Test exclusive lower bound
        target_input["exclusive-minimum"] = True
        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", json.dumps(test_json), "-j"))
        mock_random.return_value = 0.001
        ret = bosh.bosh(args=["example", json.dumps(test_json)])
        self.assertIsInstance(json.loads(ret), dict)

        # Test inclusive upper bound
        target_input["exclusive-maximum"] = False
        mock_random.return_value = 1.001
        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", json.dumps(test_json), "-j"))
        mock_random.return_value = 1
        ret = bosh.bosh(args=["example", json.dumps(test_json)])
        self.assertIsInstance(json.loads(ret), dict)

        # Test exclusive upper bound
        target_input["exclusive-maximum"] = True
        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", json.dumps(test_json), "-j"))
        mock_random.return_value = 0.999
        ret = bosh.bosh(args=["example", json.dumps(test_json)])
        self.assertIsInstance(json.loads(ret), dict)

    def test_success_json(self):
        desc_json = open(self.example1_descriptor).read()
        ret = bosh.execute("simulate", desc_json, "-j").stdout
        self.assertIsInstance(json.loads(ret), dict)
        ret = bosh.bosh(args=["example", desc_json])
        self.assertIsInstance(json.loads(ret), dict)

    def test_failing_bad_descriptor_invo_combos(self):
        self.setup("example1")
        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", self.get_file_path("fake.json"),
                           "-i", self.get_file_path("invocation.json")))

        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", self.example1_descriptor,
                           "-i", self.get_file_path("fake.json")))

        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", self.example1_descriptor,
                           "-i", self.get_file_path("exampleTool1.py")))

        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", self.example1_descriptor))

        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", self.example1_descriptor,
                           "-i", self.get_file_path("invocation.json")))

        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", self.example1_descriptor))

    def test_collapsing_whitespace_optionals(self):
        self.setup("example")
        descriptor = self.get_file_path('test_example_descriptor.json')
        command = ("bosh exec simulate " + descriptor + " -c")
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        output = str(process.stdout.read())
        command = re.search(r"(test[ \da-z]+)", output).group(0)

        self.assertNotIn("  ", command)

    def test_collapsing_whitespace_requireds(self):
        self.setup("example")
        descriptor = self.get_file_path('test_example_descriptor.json')
        command = ("bosh exec simulate " + descriptor)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        output = str(process.stdout.read())
        command = re.search(r"(test[ \da-z]+)", output).group(0)

        self.assertNotIn("  ", command)

    def test_consistency_withAndWithout_invoc(self):
        descriptor = self.get_file_path('test_simulate_consistency.json')
        noInvoc = bosh.execute("simulate", descriptor).stdout
        wInvoc = bosh.execute("simulate", descriptor, "-i",
                              bosh.example(descriptor)).stdout
        self.assertEqual(noInvoc, wInvoc)

    def test_consistency_withAndWithout_invoc_withConfigFile(self):
        descriptor = self.get_file_path(
            'test_simulate_consistency_configFile.json')
        invoc = "tmpInvoc.json"
        config = "tmpConfig.toml"
        wInvocCommand = ("bosh example {0}" +
                         " > {1} " +
                         " && bosh exec simulate {0} -i {1}").format(descriptor,
                                                                     invoc)
        noInvocCommand = "bosh exec simulate {0}".format(descriptor, invoc)

        subprocess.call(wInvocCommand, shell=True)
        with open(config, "r+") as configFile:
            wInvoc = configFile.readlines()
            os.remove(config)
            os.remove(invoc)

        subprocess.call(noInvocCommand, shell=True)
        with open(config, "r+") as configFile:
            noInvoc = configFile.readlines()
            os.remove(config)

        self.assertEqual(wInvoc, noInvoc)

    def test_list_separator(self):
        ret = bosh.execute("simulate",
                           self.get_file_path("list_separator.json"),
                           "-i",
                           self.get_file_path("list_separator_inv.json"))
        self.assertIn('1:2:3', ret.stdout)
        self.assertIn('foo.txt,bar.m', ret.stdout)

    def test_no_spaces(self):
        ret = bosh.execute("simulate",
                           self.get_file_path("no_spaces.json"))
        self.assertNotIn(' ', ret.stdout)
