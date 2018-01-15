#!/usr/bin/env python

import os, subprocess
from unittest import TestCase
from boutiques import __file__ as bfile
from boutiques.bosh import bosh

class TestBosh(TestCase):

    def test_help(self):
        self.assertRaises(SystemExit, bosh, [])
        self.assertRaises(SystemExit, bosh, ["--help"])
        self.assertRaises(SystemExit, bosh, ["exec", "--help"])
        self.assertRaises(SystemExit, bosh, ["exec", "launch",
                                             "--help"])
        self.assertRaises(SystemExit, bosh, ["exec", "simulate",
                                             "--help"])
        self.assertRaises(SystemExit, bosh, ["publish", "--help"])
        self.assertRaises(SystemExit, bosh, ["import", "--help"])
        self.assertRaises(SystemExit, bosh, ["validate", "--help"])
        self.assertRaises(SystemExit, bosh, ["invocation", "--help"])

