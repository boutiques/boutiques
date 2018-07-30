#!/usr/bin/env python

from argparse import ArgumentParser
from unittest import TestCase
from boutiques.bosh import bosh
from boutiques import __file__ as bfile
import boutiques.creator as bc
import subprocess
import os.path as op
import os

from boutiques.creator import CreatorError


class TestCreator(TestCase):

    def test_success_template(self):
        fil = 'creator_output.json'
        descriptor = bosh(['create', fil])
        assert bosh(['validate', fil]) is None

    def test_not_an_argparser(self):
        self.assertRaises(CreatorError, bc.CreateDescriptor, "notaparser")

    def test_success_argparser(self):
        parser = ArgumentParser(description="my tool description")
        parser.add_argument('myarg1', action="store",
                            help="my help 1", type=list)
        parser.add_argument('myarg2', action="store",
                            help="my help 2", type=int)
        parser.add_argument("--myarg3", "-m", action="store",
                            help="my help 3")
        subparser = parser.add_subparsers(help="the choices you will make")
        sb1 = subparser.add_parser("option1", help="the first value")
        sb1.add_argument("suboption1", help="the first sub option option")
        sb1.add_argument("suboption2", help="the first sub option option",
                         choices=['hello', 'goodbye'], default="hello")

        sb1 = subparser.add_parser("option2", help="the second value")
        sb1.add_argument("suboption1", help="the first sub option option")
        sb1.add_argument("suboption3", help="the second sub option option")
        sb1.add_argument("--suboptionflag1", "-s", help="the bool opt flag")
        sb1.add_argument("--suboptionflag2", "-d", action="store_true",
                         help="the second sub option flag")

        creatorObj = bc.CreateDescriptor(parser,
                                         execname='/path/to/myscript.py',
                                         verbose=True,
                                         tags={"purpose": "testing-creator",
                                               "foo": "bar"})
        fil = './test-created-argparse-descriptor.json'
        creatorObj.save(fil)
        assert bosh(['validate', fil]) is None
