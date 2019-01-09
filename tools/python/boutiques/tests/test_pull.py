from boutiques.bosh import bosh
from unittest import TestCase
from boutiques.puller import ZenodoError
import os
import mock
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord


def mock_get():
    mock_record = MockZenodoRecord(1472823, "Example Boutiques Tool", "",
                                   "https://zenodo.org/api/files/"
                                   "e5628764-fc57-462e-9982-65f8d6fdb487/"
                                   "example1_docker.json")
    return mock_zenodo_search([mock_record])


def mock_get_not_found():
    return mock_zenodo_search([])


class TestPull(TestCase):

    @mock.patch('requests.get', return_value=mock_get())
    def test_pull(self, mock_get):
        bosh(["pull", "zenodo.1472823"])
        cache_dir = os.path.join(os.path.expanduser('~'), ".cache", "boutiques")
        assert(os.path.exists(os.path.join(cache_dir, "zenodo-1472823.json")))

    @mock.patch('requests.get', return_value=mock_get())
    def test_pull_missing_prefix(self, mock_get):
        with self.assertRaises(ZenodoError) as e:
            bosh(["pull", "1472823"])
        assert("Zenodo ID must be prefixed by 'zenodo'" in str(e.exception))

    @mock.patch('requests.get', return_value=mock_get_not_found())
    def test_pull_not_found(self, mock_get):
        with self.assertRaises(ZenodoError) as e:
            bosh(["pull", "zenodo.99999"])
        assert("Descriptor not found" in str(e.exception))
