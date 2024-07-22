#!/usr/bin/env python

import os
from argparse import ArgumentParser
from unittest import mock

import pytest
from boutiques_mocks import MockZenodoRecord, mock_zenodo_search

import boutiques as bosh
import boutiques.creator as bc
from boutiques import __file__ as bfile
from boutiques.tests.BaseTest import BaseTest
from boutiques.util.utils import LoadError


def mock_get(*args, **kwargs):
    query = args[0].split("=")[1]
    query = query[: query.find("&")]
    query = query.replace("*", "")

    mock_records = []
    # Return an arbitrary list of results
    for i in range(0, 10):
        mock_records.append(MockZenodoRecord(i, "Example Tool %s" % i))
    return mock_zenodo_search(mock_records)


class TestLogger(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup(
            os.path.join(
                os.path.dirname(bfile), "schema", "examples", "example1"
            )
        )

    # Captures the stdout and stderr during test execution
    # and returns them as a tuple in readouterr()
    @pytest.fixture(autouse=True)
    def capture_st(self, capfd):
        self.capfd = capfd

    def test_raise_error(self):
        invocationStr = "invalid json string"
        with pytest.raises(LoadError) as e:
            bosh.execute(
                "launch",
                self.example1_descriptor,
                invocationStr,
                "--skip-data-collection",
            )
        self.assertIn("[ ERROR ]", str(e.getrepr(style="long")))

    @mock.patch("requests.get", side_effect=mock_get)
    def test_print_info(self, mock_get):
        bosh.search("-v")
        out, err = self.capfd.readouterr()
        self.assertIn("[ INFO ]", out)
        self.assertIn("[ INFO (200) ", out)

    def test_print_warning(self):
        parser = ArgumentParser(description="my tool description")
        parser.add_argument(
            "--myarg",
            "-m",
            action="store",
            help="my help",
            dest="==SUPPRESS==",
        )
        creatorObj = bc.CreateDescriptor(
            parser,
            execname="/path/to/myscript.py",
            verbose=True,
            tags={"purpose": "testing-creator", "foo": "bar"},
        )
        out, err = self.capfd.readouterr()
        self.assertIn("[ WARNING ]", out)

    def test_evaloutput(self):
        query = bosh.evaluate(
            self.example1_descriptor,
            self.get_file_path("invocation.json"),
            "invalid-query",
        )
        out, err = self.capfd.readouterr()
        self.assertIn("[ ERROR ]", out)
