#!/usr/bin/env python

from unittest import TestCase
from boutiques.bosh import bosh
from boutiques import __file__ as bfile
import os
import subprocess


class TestInvocation(TestCase):

    def test_invocation(self):
        descriptor = os.path.join(os.path.split(bfile)[0],
                                  "schema/examples/good.json")
        invocation = os.path.join(os.path.split(bfile)[0],
                                  "schema/examples/good_invocation.json")
        self.assertFalse(bosh(["invocation", descriptor, "-i",
                               invocation, "-w"]))
        self.assertFalse(bosh(["invocation", descriptor, "-i",
                               invocation, "-w"]))

    def test_invocation_invalid_cli(self):
        descriptor = os.path.join(os.path.split(bfile)[0],
                                  "schema/examples/good.json")
        invocation = os.path.join(os.path.split(bfile)[0],
                                  "schema/examples/wrong_invocation.json")
        command = ("bosh invocation " + descriptor + "-i " + invocation)
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate()
        self.assertTrue(process.returncode)
