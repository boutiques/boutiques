#!/usr/bin/env python

import subprocess, pytest
import os.path as op
from unittest import TestCase
from boutiques import __file__ as bfile
from boutiques import bosh
from jsonschema.exceptions import ValidationError

class TestTest(TestCase):

    def get_examples_dir(self):
        return op.join(op.dirname(bfile),
                       "schema", "examples")
    
    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(), reason="Docker not installed")
    def test_test_good(self):
        self.assertFalse(bosh(["test",
                               op.join(self.get_examples_dir(), "tests_good.json")]))

    def test_test_invalid(self):
        with self.assertRaises(ValidationError) as context:
           bosh(["test",
                 op.join(self.get_examples_dir(), "tests_invalid.json")])
        error_1 = "TestError: \"this_id_does_not_exist\" output id not found, in test \"test1\""  
        error_2 = "TestError: \"logfile\" output id cannot appear more than once within same test, in test \"test1\""
        error_3 = "TestError: \"testNameDefinedTwice\" test name is non-unique"
        self.assertTrue(error_1 in context.exception.message)
        self.assertTrue(error_2 in context.exception.message)
        self.assertTrue(error_3 in context.exception.message)
        self.assertTrue(context.exception.message.count("TestError") == 3)

    # Each of the following tests verify that pytest return with an exit-code of '1'.
    # According to the pytest documentation, an exit-code of '1' indicate that some _and not all_ of the tests have failed.
    # However, as each of the descriptors used for the following tests define only one test, we can safely assume that such an exit-code would indicate complete test failure.

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(), reason="Docker not installed")
    def test_test_failure_mismatched_exitcode(self):
        self.assertEqual(1, bosh(["test",
                                  op.join(self.get_examples_dir(), "tests_failure_exitcode.json")]))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(), reason="Docker not installed")
    def test_test_failure_mismatched_reference_content(self):
        self.assertEqual(1, bosh(["test",
                                  op.join(self.get_examples_dir(), "tests_failure_reference.json")]))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(), reason="Docker not installed")
    def test_test_failure_unproduced_output(self):
        self.assertEqual(1, bosh(["test",
                                  op.join(self.get_examples_dir(), "tests_failure_output_id.json")]))
