#!/usr/bin/env python

import os
import pytest
import json
import boutiques as bosh
import boutiques.creator as bc
from boutiques import __file__ as bfile
from boutiques.localExec import ExecutorError
from argparse import ArgumentParser
from unittest import TestCase
import mock
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord


def mock_get(*args, **kwargs):
    query = args[0].split("=")[1]
    query = query[:query.find("&")]
    query = query.replace("*", '')

    mock_records = []
    # Return an arbitrary list of results
    for i in range(0, 10):
        mock_records.append(MockZenodoRecord(i, "Example Tool %s" % i))
    return mock_zenodo_search(mock_records)


class TestLogger(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_raise_error(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        invocationStr = open(os.path.join(example1_dir,
                                          "invocation_invalid.json")).read()
        with pytest.raises(ExecutorError) as e:
            bosh.execute("launch",
                         os.path.join(example1_dir,
                                      "example1_docker.json"),
                         invocationStr,
                         "--skip-data-collection")
        assert("[ ERROR ]" in str(e))

    @mock.patch('requests.get', side_effect=mock_get)
    def test_print_info(self, mock_get):
        bosh.search("-v")
        out, err = self.capfd.readouterr()
        assert("[ INFO ]" in out)
        assert("[ INFO (200) " in out)

    def test_print_warning(self):
        parser = ArgumentParser(description="my tool description")
        parser.add_argument("--myarg", "-m", action="store",
                            help="my help", dest="==SUPPRESS==")
        creatorObj = bc.CreateDescriptor(parser,
                                         execname='/path/to/myscript.py',
                                         verbose=True,
                                         tags={"purpose": "testing-creator",
                                               "foo": "bar"})
        out, err = self.capfd.readouterr()
        assert("[ WARNING ]" in out)

    def test_evaloutput(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        desc = os.path.join(example1_dir, "example1_docker.json")
        invo = os.path.join(example1_dir, "invocation.json")
        query = bosh.evaluate(desc, invo, "invalid-query")
        out, err = self.capfd.readouterr()
        assert("[ ERROR ]" in out)

    # Captures the stdout and stderr during test execution
    # and returns them as a tuple in readouterr()
    @pytest.fixture(autouse=True)
    def capfd(self, capfd):
        self.capfd = capfd
