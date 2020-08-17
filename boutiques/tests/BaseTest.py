# -*- coding: utf-8 -*-
import os
import sys
import pytest
from unittest import TestCase
from boutiques import __file__ as bfile
from boutiques_mocks import example_boutiques_tool
import glob
import shutil


class BaseTest(TestCase):
    dir = "."
    tests_dir = os.path.join(os.path.dirname(bfile), "tests")
    test_temp = os.path.join(os.path.split(os.path.split(bfile)[0])[0],
                             "test_temp")
    example1_descriptor = os.path.join(os.path.dirname(bfile), "schema",
                                       "examples", "example1",
                                       "example1_docker.json")

    @pytest.fixture(autouse=True)
    def clean_test_temp(self):
        # Clean test temp directory after every test
        yield
        if os.path.exists(self.test_temp):
            shutil.rmtree(self.test_temp)

        os.makedirs(self.test_temp, exist_ok=True)

    @pytest.fixture(autouse=True)
    def reset_mock_zenodo_record(self):
        example_boutiques_tool.reset()

    def setup(self, dir):
        self.dir = dir

    def get_file_path(self, file):
        return os.path.join(
            os.path.join(
                self.tests_dir,
                self.dir),
            file)

    def assert_nothing(self, ret):
        pass

    def assert_reflected_output(self, ret):
        self.assertIn("This is stdout", ret.stdout)
        self.assertIn("This is stderr", ret.stderr)

    def assert_reflected_output_nonutf8(self, ret):
        self.assertIn("\\xc7a c'est stdout", ret.stdout)
        self.assertIn("This is std\\xe9rr", ret.stderr)

    def assert_no_output(self, ret):
        self.assertEqual(ret.stdout, "")
        self.assertEqual(ret.stderr, "")

    def assert_only_stdout(self, ret):
        self.assertNotEqual(ret.stdout, "")
        self.assertEqual(ret.stderr, "")

    def assert_successful_return(
            self,
            ret,
            required_files=None,
            required_files_len=0,
            aditional_assertions=assert_nothing):

        aditional_assertions(ret)

        self.assertEqual(ret.error_message, "")
        self.assertEqual(ret.exit_code, 0)
        self.assertEqual(ret.missing_files, [])
        if required_files is not None:
            if len(required_files) > required_files_len:
                required_files_len = len(required_files)
            self.assertEqual(len(ret.output_files),
                             required_files_len)
            for required_file in required_files:
                self.assertIn(required_file,
                              [f.file_name for f in ret.output_files])

    def assert_failed_return(self,
                             ret,
                             exit_code, error_message,
                             missing_files=[],
                             missing_file_len=0):

        if len(missing_files) > missing_file_len:
            missing_file_len = len(missing_files)

        self.assertEqual(ret.error_message, error_message)
        self.assertEqual(ret.exit_code, exit_code)
        self.assertEqual(len(ret.missing_files), missing_file_len)
        for missing in missing_files:
            self.assertIn(missing,
                          [f.file_name for f in ret.missing_files])
