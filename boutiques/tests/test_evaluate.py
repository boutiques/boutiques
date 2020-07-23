#!/usr/bin/env python

import os
from boutiques import __file__ as bfile
import boutiques as bosh
import mock
from boutiques_mocks import mock_zenodo_search, example_boutiques_tool, mock_get
from boutiques.tests.BaseTest import BaseTest
import pytest


class TestEvaluate(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup(os.path.join(os.path.dirname(bfile),
                                "schema", "examples", "example1"))

    def test_evaloutput(self):
        desc = self.example1_descriptor
        invo = self.get_file_path("invocation.json")
        query = bosh.evaluate(desc, invo, "output-files/")
        expect = {'logfile': 'log-4-coin;plop.txt',
                  'output_files': 'output/*_exampleOutputTag.resultType',
                  'config_file': './subdir1/subdir2/config.txt'}
        self.assertEqual(query, expect)

        query = bosh.evaluate(desc, invo, "output-files/id=logfile")
        expect = {'logfile': 'log-4-coin;plop.txt'}
        self.assertEqual(query, expect)

        query = bosh.evaluate(desc, invo, "output-files/id=log-file")
        expect = {}
        self.assertEqual(query, expect)

    def test_evaloutput_json_obj(self):
        desc = open(self.example1_descriptor).read()
        invo = open(self.get_file_path("invocation.json")).read()
        query = bosh.evaluate(desc, invo, "output-files/")
        expect = {'logfile': 'log-4-coin;plop.txt',
                  'output_files': 'output/*_exampleOutputTag.resultType',
                  'config_file': './subdir1/subdir2/config.txt'}
        self.assertEqual(query, expect)

        query = bosh.evaluate(desc, invo, "output-files/id=logfile")
        expect = {'logfile': 'log-4-coin;plop.txt'}
        self.assertEqual(query, expect)

        query = bosh.evaluate(desc, invo, "output-files/id=log-file")
        expect = {}
        self.assertEqual(query, expect)

    @mock.patch('requests.get', return_value=mock_get())
    def test_evaloutput_from_zenodo(self, _):
        desc = "zenodo." + str(example_boutiques_tool.id)
        invo = self.get_file_path("invocation.json")
        query = bosh.evaluate(desc, invo, "output-files/")
        expect = {'logfile': 'log-4-coin;plop.txt',
                  'output_files': 'output/*_exampleOutputTag.resultType',
                  'config_file': './config.txt'}
        self.assertEqual(query, expect)

        query = bosh.evaluate(desc, invo, "output-files/id=logfile")
        expect = {'logfile': 'log-4-coin;plop.txt'}
        self.assertEqual(query, expect)

        query = bosh.evaluate(desc, invo, "output-files/id=log-file")
        expect = {}
        self.assertEqual(query, expect)

    def test_evalinput(self):
        desc = self.example1_descriptor
        invo = self.get_file_path("invocation.json")
        query = bosh.evaluate(desc, invo, "inputs/")
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

        query = bosh.evaluate(desc, invo,
                              "inputs/type=Flag,id=flag_input",
                              "inputs/type=Number")
        expect = [{'flag_input': None},
                  {'config_num': 4,
                   'num_input': None,
                   'list_int_input': [1, 2, 3]}]
        self.assertEqual(query, expect)

        query = bosh.evaluate(desc, invo, "inputs/id=strinputs")
        expect = {}
        self.assertEqual(query, expect)

        query = bosh.evaluate(desc, invo, "inputt/nonsense=strinputs")
        expect = {}
        self.assertEqual(query, expect)

    def test_evalgroups(self):
        desc = self.example1_descriptor
        invo = self.get_file_path("invocation.json")
        query = bosh.evaluate(desc, invo, "groups/")
        expect = {'an_example_group': {'num_input': None,
                                       'enum_input': 'val1'}}
        self.assertEqual(query, expect)

        query = bosh.evaluate(desc,
                              invo,
                              "groups/mutually-exclusive=True")
        expect = {'an_example_group': {'num_input': None,
                                       'enum_input': 'val1'}}
        self.assertEqual(query, expect)
