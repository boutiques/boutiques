# -*- coding: utf-8 -*-
import os
import sys
from unittest import TestCase
from boutiques import __file__ as bfile


class BaseTest(TestCase):
    dir = "."

    def setup(self, dir):
        self.dir = dir

    def get_file_path(self, file):
        return os.path.join(
            os.path.join(
                os.path.dirname(bfile),
                "schema",
                "examples",
                self.dir),
            file)

    def assert_nothing(self, ret):
        pass

    def assert_reflected_output(self, ret):
        self.assertIn("This is stdout", ret.stdout)
        self.assertIn("This is stderr", ret.stderr)

    def assert_reflected_output_nonutf8(self, ret):
        if sys.version_info[0] < 3:
            self.assertIn("a c'est stdout", ret.stdout)
            self.assertIn("This is stdrr", ret.stderr)
        elif sys.version_info[0] == 3 and sys.version_info[1] == 4:
            self.assertIn("�a c'est stdout", ret.stdout)
            self.assertIn("This is std�rr", ret.stderr)
        else:
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
