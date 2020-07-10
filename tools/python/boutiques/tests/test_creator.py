#!/usr/bin/env python

from argparse import ArgumentParser
from unittest import TestCase
from boutiques import bosh
from boutiques import __file__ as bfile
from boutiques.util.utils import loadJson
import boutiques.creator as bc
import subprocess
import os.path as op
import simplejson as json
import os
import pytest
from boutiques.util.BaseTest import BaseTest
from boutiques.creator import CreatorError


class TestCreator(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("creator")

    def test_success_template(self):
        fil = 'creator_output.json'
        descriptor = bosh(['create', fil])
        self.assertIsNone(bosh(['validate', fil]))

    def test_success_docker(self):
        fil = 'creator_output.json'
        descriptor = bosh(['create', '-d', 'mysql:latest', fil])
        self.assertIsNone(bosh(['validate', fil]))

    def test_success_docker_sing_import(self):
        fil = 'creator_output.json'
        descriptor = bosh(['create', '-d', 'mysql:latest', '-u', fil])
        self.assertIsNone(bosh(['validate', fil]))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_fail_image_(self):
        fil = 'creator_output.json'
        self.assertRaises(CreatorError, bosh,
                          ['create', '-d', 'ihopethisdoesntexists', fil])

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

        self.assertIsNone(bosh(['validate', fil]))
        self.assertIsNone(bosh(['invocation', fil, '-i', invof]))

    def test_success_template_camel_case(self):
        template = op.join(op.split(self.tests_dir)[0],
                           'templates',
                           'basic.json')
        fil = 'creator_output.json'
        bosh(['create', fil, '--camel-case'])
        self.assertIsNone(bosh(['validate', fil]))

        desc = loadJson(fil)
        template = loadJson(template)

        # Check "_" in all instances of input indices (inputs + groups)
        for inp, camelInp in zip(template['inputs'], desc['inputs']):
            self.assertTrue("_" in inp['id'])
            self.assertFalse("_" in camelInp['id'])

        for mbrs, camelMbrs in [(grp['members'], camelGrp['members']) for
                                grp, camelGrp in
                                zip(template['groups'], desc['groups'])]:
            self.assertTrue(all([("_" in mbr) for mbr in mbrs]))
            self.assertFalse(all([("_" in camelMbr) for camelMbr in camelMbrs]))

    def test_create_cl_template_from_descriptor(self):
        cl_template = self.get_file_path("expected_cl_template_create.json")
        output = self.get_file_path("out_desc.json")
        expected_cml = loadJson(cl_template)['command-line']
        expected_inputs = loadJson(cl_template)['inputs']

        create_args = ["create", output, "--cl-template", cl_template]
        bosh(create_args)
        result_cml = loadJson(output)['command-line']
        result_inputs = loadJson(output)['inputs']

        if op.exists(output):
            os.remove(output)

        self.assertEqual(expected_cml, result_cml)
        self.assertEqual(expected_inputs, result_inputs)

    def test_create_cl_template_from_string(self):
        cl_template = self.get_file_path("expected_cl_template_create.json")
        output = self.get_file_path("out_desc.json")
        expected_cml = "echo [PARAM1] [PARAM2] [FLAG1] > [OUTPUT1]"
        expected_inputs = loadJson(cl_template)['inputs']

        create_args = ["create", output, "--cl-template", expected_cml]
        bosh(create_args)
        result_cml = loadJson(output)['command-line']
        result_inputs = loadJson(output)['inputs']

        if op.exists(output):
            os.remove(output)

        self.assertEqual(expected_cml, result_cml)
        self.assertEqual(expected_inputs, result_inputs)
