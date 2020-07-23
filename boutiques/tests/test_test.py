#!/usr/bin/env python

import subprocess
import pytest
import os.path as op
from boutiques import __file__ as bfile
from boutiques import bosh
from jsonschema.exceptions import ValidationError
import sys
import mock
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord,\
    example_boutiques_tool
from boutiques.tests.BaseTest import BaseTest


class TestTest(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("test")

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_test_good(self):
        self.assertFalse(
            bosh(["test", self.get_file_path("tests_good.json")]))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_test_good_desc_as_json_obj(self):
        self.assertFalse(
            bosh(["test", open(self.get_file_path("tests_good.json")).read()]))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    @mock.patch('requests.get',
                return_value=mock_zenodo_search([example_boutiques_tool]))
    def test_test_good_from_zenodo(self, mock_get):
        self.assertFalse(
            bosh(["test", "zenodo." + str(example_boutiques_tool.id)]))

    def test_test_invalid(self):
        with self.assertRaises(ValidationError) as context:
            bosh(["test", self.get_file_path("tests_invalid.json")])
        error_1 = "TestError: \"this_id_does_not_exist\" output id not "\
                  "found, in test \"test1\""
        error_2 = "TestError: \"logfile\" output id cannot appear more"\
                  " than once within same test, in test \"test1\""
        error_3 = "TestError: \"testNameDefinedTwice\" test name is non-unique"
        self.assertTrue(error_1 in context.exception.message)
        self.assertTrue(error_2 in context.exception.message)
        self.assertTrue(error_3 in context.exception.message)
        self.assertTrue(context.exception.message.count("TestError") == 3)

    # Each of the following tests verify that pytest return with
    # an exit-code of '1'.
    # According to the pytest documentation, an exit-code of '1'
    # indicate that some _and not all_ of the tests have failed.
    # However, as each of the descriptors used for the following tests
    # define only one test, we can safely assume that such an
    # exit-code would indicate complete test failure.

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_test_failure_mismatched_exitcode(self):
        self.assertEqual(
            1, bosh(["test",
                     self.get_file_path("tests_failure_exitcode.json")]))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_test_failure_mismatched_reference_content(self):
        self.assertEqual(
            1, bosh(["test",
                     self.get_file_path("tests_failure_reference.json")]))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_test_failure_unproduced_output(self):
        self.assertEqual(
            1, bosh(["test",
                     self.get_file_path("tests_failure_output_id.json")]))
