#!/usr/bin/env python

from argparse import ArgumentParser
from unittest import TestCase
from boutiques.bosh import bosh
from boutiques import __file__ as bfile
import boutiques.creator as bc
import subprocess
import os.path as op
import json
import os
import pytest

from boutiques.creator import CreatorError


class TestCreator(TestCase):

    def test_success_template(self):
        fil = 'creator_output.json'
        descriptor = bosh(['create', fil])
        assert bosh(['validate', fil]) is None

    def test_success_docker(self):
        fil = 'creator_output.json'
        descriptor = bosh(['create', '-d', 'mysql:latest', fil])
        assert bosh(['validate', fil]) is None

    def test_success_docker_sing_import(self):
        fil = 'creator_output.json'
        descriptor = bosh(['create', '-d', 'mysql:latest', '-u', fil])
        assert bosh(['validate', fil]) is None

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_fail_image_(self):
        fil = 'creator_output.json'
        self.assertRaises(CreatorError,
                          bosh,
                          ['create', '-d', 'ihopethisdoesntexists', fil]
                          )

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
        subparser = parser.add_subparsers(help="the choices you will make",
                                          dest="mysubparser")
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
        sb1.add_argument("--suboptlistflag", "-l", nargs="+", help="listy flag")

        creatorObj = bc.CreateDescriptor(parser,
                                         execname='/path/to/myscript.py',
                                         verbose=True,
                                         tags={"purpose": "testing-creator",
                                               "foo": "bar"})

        fil = './test-created-argparse-descriptor.json'
        creatorObj.save(fil)

        invof = './test-created-argparse-inputs.json'
        args = parser.parse_args([['val1', 'val2'], '2', 'option2',
                                  'subval1', 'subval3',
                                  '--suboptionflag1', 't1',
                                  '--suboptionflag2'])
        invo = creatorObj.createInvocation(args)
        with open(invof, 'w') as fhandle:
            fhandle.write(json.dumps(invo, indent=4))

        assert bosh(['validate', fil]) is None
        assert bosh(['invocation', fil, '-i', invof]) is None
