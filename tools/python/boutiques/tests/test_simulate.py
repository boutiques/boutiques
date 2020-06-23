#!/usr/bin/env python

import os
import re
import subprocess
from unittest import TestCase
import simplejson as json
from boutiques import __file__ as bfile
import boutiques as bosh
import mock
from boutiques.localExec import ExecutorError
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord,\
    example_boutiques_tool


def mock_get():
    return mock_zenodo_search([example_boutiques_tool])


class TestSimulate(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_success(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.assertFalse(bosh.execute("simulate",
                                      os.path.join(example1_dir,
                                                   "example1_docker.json"
                                                   )).exit_code)

        self.assertFalse(bosh.execute("simulate",
                                      os.path.join(self.get_examples_dir(),
                                                   "good_nooutputs.json"
                                                   )).exit_code)

    def test_success_desc_as_json_obj(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        desc_json = open(os.path.join(example1_dir,
                                      "example1_docker.json")).read()
        self.assertFalse(bosh.execute("simulate",
                                      desc_json).exit_code)

    @mock.patch('requests.get', return_value=mock_get())
    def test_success_desc_from_zenodo(self, mock_get):
        self.assertFalse(bosh.execute("simulate",
                                      "zenodo." +
                                      str(example_boutiques_tool.id))
                         .exit_code)

    def test_success_default_values(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.assertFalse(bosh.execute("simulate",
                                      os.path.join(example1_dir,
                                                   "example1_docker.json"),
                                      "-i",
                                      os.path.join(example1_dir,
                                                   "inv_no_defaults.json"))
                         .exit_code)

    @mock.patch('random.uniform')
    def test_number_bounds(self, mock_random):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        desc_json = open(os.path.join(example1_dir,
                                      "example1_docker.json")).read()
        test_json = json.loads(desc_json)
        del test_json['groups']
        target_input = [i for i in test_json["inputs"]
                        if i["id"] == "num_input"][0]
        target_input["optional"] = False

        # Test inclusive lower bound
        target_input["exclusive-minimum"] = False
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
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        desc_json = open(os.path.join(example1_dir,
                                      "example1_docker.json")).read()
        ret = bosh.execute("simulate", desc_json, "-j").stdout
        self.assertIsInstance(json.loads(ret), dict)
        ret = bosh.bosh(args=["example", desc_json])
        self.assertIsInstance(json.loads(ret), dict)

    def test_failing_bad_descriptor_invo_combos(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")

        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", os.path.join(example1_dir, "fake.json"),
                           "-i", os.path.join(example1_dir, "invocation.json")))

        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", os.path.join(example1_dir,
                                                    "example1_docker.json"),
                           "-i", os.path.join(example1_dir, "fake.json")))

        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", os.path.join(example1_dir,
                                                    "example1_docker.json"),
                           "-i", os.path.join(example1_dir, "exampleTool1.py")))

        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", os.path.join(example1_dir,
                                                    "example1_docker.json")))

        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", os.path.join(example1_dir,
                                                    "example1_docker.json"),
                           "-i", os.path.join(example1_dir, "invocation.json")))

        self.assertRaises(ExecutorError, bosh.execute,
                          ("simulate", os.path.join(example1_dir,
                                                    "example1_docker.json")))

    def test_collapsing_whitespace_optionals(self):
        descriptor = os.path.join(os.path.split(bfile)[0],
                                  'schema/examples/'
                                  'example-invocation/'
                                  'example_descriptor.json')
        command = ("bosh exec simulate " + descriptor + " -c")
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        output = str(process.stdout.read())
        command = re.search(r"(test[ \da-z]+)", output).group(0)

        self.assertNotIn("  ", command)

    def test_collapsing_whitespace_requireds(self):
        descriptor = os.path.join(os.path.split(bfile)[0],
                                  'schema/examples/'
                                  'example-invocation/'
                                  'example_descriptor.json')
        command = ("bosh exec simulate " + descriptor)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        output = str(process.stdout.read())
        command = re.search(r"(test[ \da-z]+)", output).group(0)

        self.assertNotIn("  ", command)

    def test_consistency_withAndWithout_invoc(self):
        descriptor = os.path.join(os.path.split(bfile)[0],
                                  'schema/examples/'
                                  'test_simulate_consistency.json')
        noInvoc = bosh.execute("simulate", descriptor).stdout
        wInvoc = bosh.execute("simulate", descriptor, "-i",
                              bosh.example(descriptor)).stdout
        self.assertEqual(noInvoc, wInvoc)

    def test_consistency_withAndWithout_invoc_withConfigFile(self):
        descriptor = os.path.join(os.path.split(bfile)[0],
                                  'schema/examples/'
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
