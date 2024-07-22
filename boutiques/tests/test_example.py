#!/usr/bin/env python

import subprocess

import pytest
import simplejson as json

from boutiques.tests.BaseTest import BaseTest


class TestExample(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("example")

    def test_example_complete(self):
        descriptor = self.get_file_path('test_example_descriptor.json')
        command = ("bosh example " + descriptor + " -c")
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        output = json.loads(process.stdout.read())

        self.assertTrue(("a1" in output and "b2" in output) or "a2" in output)
        self.assertIn("b1", output)
        self.assertIn("c1", output)
        self.assertIn("c2", output)
        self.assertIn("d1", output)
        self.assertIn("d2", output)

    def test_example_required_only(self):
        descriptor = self.get_file_path('test_example_descriptor.json')
        command = ("bosh example " + descriptor)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE)
        output = json.loads(process.stdout.read())

        self.assertDictEqual({"b1": "b1", "c2": "c2"}, output)

    def test_example_requires_group_complete_x10(self):
        descriptor = self.get_file_path('test_docopt_valid.json')
        from boutiques.localExec import LocalExecutor
        executor = LocalExecutor(descriptor, None,
                                 {"forcePathType": True,
                                  "destroyTempScripts": True,
                                  "changeUser": True,
                                  "skipDataCollect": True,
                                  "requireComplete": True,
                                  "sandbox": False})

        # Can't create descriptors with mutex group but only one valid example
        # Bosh example is inherently random,
        # Couldn't even inject prederemined input to executor.in_dict
        # because _randomFillInDict clears it
        for _ in range(0, 10):
            executor.generateRandomParams()
            self.assertGreater(len(executor.in_dict), 0)
            executor.in_dict = None
