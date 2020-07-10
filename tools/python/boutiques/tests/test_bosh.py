#!/usr/bin/env python
from boutiques.bosh import bosh
from boutiques.localExec import ExecutorError
from boutiques.dataHandler import DataHandlerError
from boutiques import BoutiquesError
from boutiques.util.BaseTest import BaseTest


class TestBosh(BaseTest):

    def test_help(self):
        self.assertRaises(ExecutorError, bosh, [])
        self.assertRaises(ExecutorError, bosh, ["--help"])
        self.assertRaises(ExecutorError, bosh, ["exec", "--help"])
        self.assertRaises(ExecutorError, bosh, ["exec", "launch", "--help"])
        self.assertRaises(ExecutorError, bosh, ["exec", "simulate", "--help"])
        self.assertRaises(ExecutorError, bosh, ["exec", "prepare", "--help"])
        self.assertRaises(DataHandlerError, bosh, ["data", "--help"])
        self.assertRaises(DataHandlerError, bosh, ["data", "delete", "--help"])
        self.assertRaises(DataHandlerError, bosh, ["data", "inspect", "--help"])
        self.assertRaises(DataHandlerError, bosh, ["data", "publish", "--help"])
        self.assertRaises(BoutiquesError, bosh, ["publish", "--help"])
        self.assertRaises(BoutiquesError, bosh, ["import", "--help"])
        self.assertRaises(BoutiquesError, bosh, ["validate", "--help"])
        self.assertRaises(BoutiquesError, bosh, ["invocation", "--help"])
        self.assertRaises(BoutiquesError, bosh, ["evaluate", "--help"])
        self.assertRaises(BoutiquesError, bosh, ["create", "--help"])
        self.assertRaises(BoutiquesError, bosh, ["example", "--help"])
