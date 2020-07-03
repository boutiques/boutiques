from boutiques.bosh import bosh
from unittest import TestCase
import os
import mock
import json
from boutiques import __file__ as bfile
from boutiques.util.utils import loadJson
from boutiques.deprecate import DeprecateError, deprecate
from boutiques_mocks import *


@mock.patch('requests.get', side_effect=mock_get)
@mock.patch('requests.post', side_effect=mock_post)
@mock.patch('requests.put', side_effect=mock_put)
@mock.patch('requests.delete', side_effect=mock_delete)
class TestDeprecate(TestCase):
    def test_deprecate(self, *args):
        new_doi = bosh(["deprecate", "--verbose", "--by", "zenodo.12345",
                        "zenodo." + str(example_boutiques_tool.id),
                        "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                        "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue(new_doi)

    def test_deprecate_no_by(self, *args):
        new_doi = bosh(["deprecate", "--verbose",
                        "zenodo." + str(example_boutiques_tool.id),
                        "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                        "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue(new_doi)

    def test_deprecate_by_inexistent(self, *args):
        with self.assertRaises(DeprecateError) as e:
            new_doi = bosh(["deprecate", "--verbose", "--by", "zenodo.00000",
                            "zenodo." + str(example_boutiques_tool.id),
                            "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                            "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue("Tool does not exist" in str(e.exception))

    def test_deprecate_deprecated(self, *args):
        new_doi = deprecate(zenodo_id="zenodo.11111",
                            sandbox=True,
                            verbose=True,
                            zenodo_token="hAaW2wSBZMskxpfigTYHcuDrC"
                            "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r",
                            download_function=mock_download_deprecated)
        self.assertTrue(new_doi)

    def test_deprecate_previous_version(self, *args):
        with self.assertRaises(DeprecateError) as e:
            new_doi = bosh(["deprecate", "--verbose",
                            "zenodo.22222",
                            "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                            "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue("Tool zenodo.22222 has a newer version"
                        in str(e.exception))
