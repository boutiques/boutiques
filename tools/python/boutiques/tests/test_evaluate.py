#!/usr/bin/env python

import os
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh
import mock
from boutiques_mocks import mock_zenodo_search, example_boutiques_tool
from boutiques.util.BaseTest import BaseTest
import pytest


def get_examples(schema_examples_dir):
    example1_dir = os.path.join(schema_examples_dir, "example1")
    yield os.path.join(example1_dir, "example1_docker.json")
    yield os.path.join(example1_dir, "invocation.json")


def get_examples_json_obj(schema_examples_dir):
    example1_dir = os.path.join(schema_examples_dir, "example1")
    yield open(os.path.join(example1_dir, "example1_docker.json")).read()
    yield open(os.path.join(example1_dir, "invocation.json")).read()


def get_examples_from_zenodo(schema_examples_dir):
    example1_dir = os.path.join(schema_examples_dir, "example1")
    yield "zenodo." + str(example_boutiques_tool.id)
    yield os.path.join(example1_dir, "invocation.json")


class TestEvaluate(BaseTest):

    def test_evaloutput(self):
        self.desc, self.invo = get_examples(self.tests_dir)
        query = bosh.evaluate(self.desc, self.invo, "output-files/")
        expect = {'logfile': 'log-4-coin;plop.txt',
                  'output_files': 'output/*_exampleOutputTag.resultType',
                  'config_file': './subdir1/subdir2/config.txt'}
        self.assertEqual(query, expect)

        query = bosh.evaluate(self.desc, self.invo, "output-files/id=logfile")
        expect = {'logfile': 'log-4-coin;plop.txt'}
        self.assertEqual(query, expect)

        query = bosh.evaluate(self.desc, self.invo, "output-files/id=log-file")
        expect = {}
        self.assertEqual(query, expect)

    def test_evaloutput_json_obj(self):
        self.desc, self.invo = get_examples_json_obj(self.tests_dir)
        query = bosh.evaluate(self.desc, self.invo, "output-files/")
        expect = {'logfile': 'log-4-coin;plop.txt',
                  'output_files': 'output/*_exampleOutputTag.resultType',
                  'config_file': './subdir1/subdir2/config.txt'}
        self.assertEqual(query, expect)

        query = bosh.evaluate(self.desc, self.invo, "output-files/id=logfile")
        expect = {'logfile': 'log-4-coin;plop.txt'}
        self.assertEqual(query, expect)

        query = bosh.evaluate(self.desc, self.invo, "output-files/id=log-file")
        expect = {}
        self.assertEqual(query, expect)

    @mock.patch('requests.get',
                return_value=mock_zenodo_search([example_boutiques_tool]))
    def test_evaloutput_from_zenodo(self, _):
        self.desc, self.invo =\
            get_examples_from_zenodo(self.tests_dir)
        query = bosh.evaluate(self.desc, self.invo, "output-files/")
        expect = {'logfile': 'log-4-coin;plop.txt',
                  'output_files': 'output/*_exampleOutputTag.resultType',
                  'config_file': './config.txt'}
        self.assertEqual(query, expect)

        query = bosh.evaluate(self.desc, self.invo, "output-files/id=logfile")
        expect = {'logfile': 'log-4-coin;plop.txt'}
        self.assertEqual(query, expect)

        query = bosh.evaluate(self.desc, self.invo, "output-files/id=log-file")
        expect = {}
        self.assertEqual(query, expect)

    def test_evalinput(self):
        self.desc, self.invo = get_examples(self.tests_dir)
        query = bosh.evaluate(self.desc, self.invo, "inputs/")
        expect = {'str_input_list': ["fo '; echo FAIL", 'bar'],
                  'str_input': 'coin;plop',
                  'config_num': 4,
                  'num_input': None,
                  'file_input': './setup.py',
                  'file_list_input': ['/test_mount1', '/test_mount2'],
                  'enum_input': 'val1',
                  'list_int_input': [1, 2, 3],
                  'flag_input': None,
                  'no_opts': None}
        self.assertEqual(query, expect)

        query = bosh.evaluate(self.desc, self.invo,
                              "inputs/type=Flag,id=flag_input",
                              "inputs/type=Number")
        expect = [{'flag_input': None},
                  {'config_num': 4,
                   'num_input': None,
                   'list_int_input': [1, 2, 3]}]
        self.assertEqual(query, expect)

        query = bosh.evaluate(self.desc, self.invo, "inputs/id=strinputs")
        expect = {}
        self.assertEqual(query, expect)

        query = bosh.evaluate(self.desc, self.invo, "inputt/nonsense=strinputs")
        expect = {}
        self.assertEqual(query, expect)

    def test_evalgroups(self):
        self.desc, self.invo = get_examples(self.tests_dir)
        query = bosh.evaluate(self.desc, self.invo, "groups/")
        expect = {'an_example_group': {'num_input': None,
                                       'enum_input': 'val1'}}
        self.assertEqual(query, expect)

        query = bosh.evaluate(self.desc,
                              self.invo,
                              "groups/mutually-exclusive=True")
        expect = {'an_example_group': {'num_input': None,
                                       'enum_input': 'val1'}}
        self.assertEqual(query, expect)
