#!/usr/bin/env python

import os
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh


class TestEvaluate(TestCase):

    def set_examples(self):
        example1_dir = os.path.join(os.path.dirname(bfile), "schema",
                                    "examples", "example1")
        self.desc = os.path.join(example1_dir, "example1_docker.json")
        self.invo = os.path.join(example1_dir, "invocation.json")

    def test_evaloutput(self):
        self.set_examples()
        query = bosh.evaluate(self.desc, self.invo, "output-files/")
        expect = {'logfile': 'log-4.txt',
                  'output_files': 'output/*_exampleOutputTag.resultType',
                  'config_file': './config.txt'}
        assert(query == expect)

        query = bosh.evaluate(self.desc, self.invo, "output-files/id=logfile")
        expect = {'logfile': 'log-4.txt'}
        assert(query == expect)

        query = bosh.evaluate(self.desc, self.invo, "output-files/id=log-file")
        expect = {}
        assert(query == expect)

    def test_evalinput(self):
        self.set_examples()
        query = bosh.evaluate(self.desc, self.invo, "inputs/")
        expect = {'str_input': ['foo', 'bar'],
                  'config_num': 4,
                  'num_input': None,
                  'file_input': './setup.py',
                  'enum_input': 'val1',
                  'list_int_input': [1, 2, 3],
                  'flag_input': None}
        assert(query == expect)

        query = bosh.evaluate(self.desc, self.invo,
                              "inputs/type=Flag,id=flag_input",
                              "inputs/type=Number")
        expect = [{'flag_input': None},
                  {'config_num': 4,
                   'num_input': None,
                   'list_int_input': [1, 2, 3]}]
        assert(query == expect)

        query = bosh.evaluate(self.desc, self.invo, "inputs/id=strinputs")
        expect = {}
        assert(query == expect)

        query = bosh.evaluate(self.desc, self.invo, "inputt/nonsense=strinputs")
        expect = {}
        assert(query == expect)

    def test_evalgroups(self):
        self.set_examples()
        query = bosh.evaluate(self.desc, self.invo, "groups/")
        expect = {'an_example_group': {'num_input': None,
                                       'enum_input': 'val1'}}
        assert(query == expect)

        query = bosh.evaluate(self.desc,
                              self.invo,
                              "groups/mutually-exclusive=True")
        expect = {'an_example_group': {'num_input': None,
                                       'enum_input': 'val1'}}
        assert(query == expect)
