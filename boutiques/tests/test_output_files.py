#!/usr/bin/env python

import os
import subprocess

import pytest
import simplejson as json

from boutiques.tests.BaseTest import BaseTest


class TestOutputFiles(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("output_files")

    @pytest.fixture(autouse=True)
    def clean_up(self):
        yield
        if os.path.exists(self.get_file_path("get_test_desc.json")):
            os.remove(self.get_file_path("get_test_desc.json"))

    def test_output_conditional_path_template_validity(self):
        test_desc_path = self.get_file_path("test_fixANDcond_output_desc.json")

        # Validate descriptor with output-files containing both conditional
        # and fixed path-templates objects
        command = "bosh validate " + test_desc_path
        validate = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE
        )
        output = validate.stdout.read()
        self.assertEqual(b"OK\n", output)

    def test_conditional_path_template_mutual_exclusivity(self):
        base_desc_path = self.get_file_path("test_fixANDcond_output_desc.json")
        test_desc_path = self.get_file_path("test_desc.json")

        template_desc_json = {}
        with open(base_desc_path) as base_desc:
            template_desc_json = json.load(base_desc)

        test_json = {
            k: template_desc_json[k]
            for k in template_desc_json
            if k != "output-files"
        }
        output_list = template_desc_json["output-files"]

        # Test descriptor with only path template output file
        test_json["output-files"] = [
            out for out in output_list if "path-template" in out
        ]
        with open(test_desc_path, "w+") as test_desc:
            test_desc.write(json.dumps(test_json))
        command = "bosh validate " + test_desc_path
        validate_only_PT = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE
        )
        process_output = validate_only_PT.stdout.read()
        self.assertEqual(b"OK\n", process_output)

        # Test descriptor with only conditional path template output file
        test_json["output-files"] = [
            out for out in output_list if "path-template" not in out
        ]
        with open(test_desc_path, "w+") as test_desc:
            test_desc.write(json.dumps(test_json))
        validate_only_CPT = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE
        )
        process_output = validate_only_CPT.stdout.read()
        self.assertEqual(b"OK\n", process_output)

        # Test descriptor with output-files object containing both \
        # conditional and fixed path-templates
        test_json["output-files"][0]["path-template"] = "[PARAM1]/out1.txt"
        with open(test_desc_path, "w+") as test_desc:
            test_desc.write(json.dumps(test_json))
        validate_fixANDCond = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE
        )
        process_output = validate_fixANDCond.stdout.read()
        self.assertIn("[ ERROR ]", process_output.decode())
        self.assertIn("schema", process_output.decode())

    def test_conditional_path_template_optionality(self):
        base_desc_path = self.get_file_path("test_fixANDcond_output_desc.json")
        test_desc_path = self.get_file_path("test_desc.json")

        template_desc_json = {}
        with open(base_desc_path) as base_desc:
            template_desc_json = json.load(base_desc)

        test_json = {
            k: template_desc_json[k]
            for k in template_desc_json
            if k != "output-files"
        }
        output_list = template_desc_json["output-files"]

        # Test non-optional conditional-path-template with missing default
        test_json["output-files"] = [
            out for out in output_list if "path-template" not in out
        ]
        test_json["output-files"][0]["conditional-path-template"].remove(
            {"default": "[PARAM2]_default.txt"}
        )
        with open(test_desc_path, "w+") as test_desc:
            test_desc.write(json.dumps(test_json))
        command = "bosh validate " + test_desc_path
        validate_missing_default = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE
        )
        process_output = validate_missing_default.stdout.read()
        self.assertIn(
            'OutputError: "out2". Non-optional output-file with '
            "conditional-path-template must contain "
            '"default" path-template.',
            process_output.decode(),
        )

        # Test duplicate default condition in CPT
        test_json["output-files"][0]["conditional-path-template"].extend(
            [
                {"default": "[PARAM2]_default.txt"},
                {"default": "[PARAM1]_default.txt"},
            ]
        )
        with open(test_desc_path, "w+") as test_desc:
            test_desc.write(json.dumps(test_json))
        validate_duplicate_default = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE
        )
        process_output = validate_duplicate_default.stdout.read()
        self.assertIn(
            'OutputError: "out2". Only one "default" condition '
            "is permitted in a conditional-path-template.",
            process_output.decode(),
        )

    def test_conditional_path_template_expressions(self):
        base_desc_path = self.get_file_path("test_fixANDcond_output_desc.json")
        test_desc_path = self.get_file_path("test_desc.json")

        template_desc_json = {}
        with open(base_desc_path) as base_desc:
            template_desc_json = json.load(base_desc)

        test_json = {
            k: template_desc_json[k]
            for k in template_desc_json
            if k != "output-files"
        }
        output_list = template_desc_json["output-files"]

        # Test non-optional conditional-path-template with wrong ID name
        test_json["output-files"] = [
            out for out in output_list if "path-template" not in out
        ]
        test_json["output-files"][0]["conditional-path-template"].append(
            {"bob": "invalid.txt"}
        )
        with open(test_desc_path, "w+") as test_desc:
            test_desc.write(json.dumps(test_json))
        command = "bosh validate " + test_desc_path
        validate_wrong_ID = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE
        )
        process_output = validate_wrong_ID.stdout.read()
        self.assertIn(
            'OutputError: "out2" contains non-python '
            'keyword and non-ID string: "bob"',
            process_output.decode(),
        )

    def test_conditional_path_template_comparison_types(self):
        test_desc_path = self.get_file_path(
            "test_cond_output_invalid_types.json"
        )

        command = "bosh validate " + test_desc_path
        validate_wrong_ID = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE
        )
        process_output = validate_wrong_ID.stdout.read()
        self.assertIn(
            '"opt1 and (opt2 > "10.00")" contains '
            "invalid conditional expression.",
            process_output.decode(),
        )
        self.assertIn(
            '"opt1 and opt2 and (opt1 == "False")" contains '
            "invalid conditional expression.",
            process_output.decode(),
        )
        self.assertIn(
            '"param1 < 10.0" contains ' "invalid conditional expression.",
            process_output.decode(),
        )
