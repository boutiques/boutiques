#!/usr/bin/env python

import sys
from boutiques.descriptor2func import function
if sys.version_info < (2, 7):
    from unittest2 import TestCase
else:
    from unittest import TestCase


class TestDesc2func(TestCase):

    def test_desc2func(self):
        mcflirt = function('zenodo.2602109', mode='simulate')
        res = mcflirt(in_file='/tmp/test.nii.gz')
        self.assertEqual(res.shell_command.strip(),
                         'mcflirt -in /tmp/test.nii.gz')
        self.assertEqual(res.container_location, 'hide')
        self.assertEqual(res.container_command, '')
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.stdout.strip(), 'mcflirt -in /tmp/test.nii.gz')
        self.assertEqual(res.error_message, '')
        self.assertEqual(res.output_files, [])
        self.assertEqual(res.missing_files, [])
