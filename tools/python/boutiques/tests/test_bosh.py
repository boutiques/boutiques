#!/usr/bin/env python
from unittest import TestCase
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
        self.assertRaises(SystemExit, bosh, ["evaluate", "--help"])
        self.assertRaises(SystemExit, bosh, ["create", "--help"])
        self.assertRaises(SystemExit, bosh, ["example", "--help"])
