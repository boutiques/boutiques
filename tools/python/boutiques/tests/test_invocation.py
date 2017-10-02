#!/usr/bin/env python

from unittest import TestCase
from boutiques.bosh import bosh
from boutiques import __file__ as bfile
import os, subprocess

class TestInvocation(TestCase):

    def test_invocation(self):
        descriptor = os.path.join(os.path.split(bfile)[0], "schema/examples/good.json")
        invocation = os.path.join(os.path.split(bfile)[0], "schema/examples/good_invocation.json")
        self.assertFalse(bosh(["invocation", descriptor, "-i", invocation]))
        self.assertFalse(bosh(["invocation", descriptor, "-i", invocation]))
