#!/usr/bin/env python

from unittest import TestCase
from boutiques.invocationSchemaHandler import main
from boutiques import __file__ as bofile
import os

class TestImport(TestCase):

    def test_invocation(self):
        tool = os.path.join(os.path.split(bofile)[0], "schema/examples/good.json")
        invocation = os.path.join(os.path.split(bofile)[0], "schema/examples/good_invocation.json")
        self.assertFalse(main(args=[tool,'-i',invocation]))

        
