from boutiques.bosh import bosh
from unittest import TestCase
from boutiques.puller import ZenodoError
import os
import mock
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord


def mock_get(*args, **kwargs):
    mock_record1 = MockZenodoRecord(1472823, "Example Boutiques Tool", "",
                                    "https://zenodo.org/api/files/"
                                    "e5628764-fc57-462e-9982-65f8d6fdb487/"
                                    "example1_docker.json")
    mock_record2 = MockZenodoRecord(2587160, "makeblastdb", "",
                                    "https://zenodo.org/api/files/"
                                    "d861b2cd-ec68-4613-9847-1911904a1218/"
                                    "makeblastdb.json")
    if "1472823" in args[0]:
        return mock_zenodo_search([mock_record1])
    if "2587160" in args[0]:
        return mock_zenodo_search([mock_record2])
    return mock_zenodo_search([])


class TestPull(TestCase):

    @mock.patch('requests.get', side_effect=mock_get)
    def test_pull(self, mock_get):
        bosh(["pull", "zenodo.1472823"])
        cache_dir = os.path.join(os.path.expanduser('~'), ".cache", "boutiques")
        assert(os.path.exists(os.path.join(cache_dir, "zenodo-1472823.json")))

    @mock.patch('requests.get', side_effect=mock_get)
    def test_pull_multi(self, mock_get):
        results = bosh(["pull", "zenodo.1472823", "zenodo.2587160"])
        cache_dir = os.path.join(os.path.expanduser('~'), ".cache", "boutiques")
        self.assertTrue(os.path.exists(os.path.join(cache_dir,
                                                    "zenodo-1472823.json")))
        self.assertTrue(os.path.exists(os.path.join(cache_dir,
                                                    "zenodo-2587160.json")))
        self.assertEqual(len(results), 2, results)

    @mock.patch('requests.get', side_effect=mock_get)
    def test_pull_duplicate_collapses(self, mock_get):
        results = bosh(["pull", "zenodo.1472823", "zenodo.2587160",
                        "zenodo.2587160"])
        self.assertEqual(len(results), 2, results)

    @mock.patch('requests.get', side_effect=mock_get)
    def test_pull_missing_raises_exception(self, mock_get):
        good1 = "zenodo.1472823"
        good2 = "zenodo.2587160"
        bad1 = "zenodo.9999990"
        with self.assertRaises(ZenodoError) as e:
            bosh(["pull", good1, bad1, good2])
        self.assertIn("Descriptor \"{0}\" not found".format(
            bad1.split(".")[1]),
            str(e.exception))

    @mock.patch('requests.get', side_effect=mock_get)
    def test_pull_missing_prefix(self, mock_get):
        with self.assertRaises(ZenodoError) as e:
            bosh(["pull", "1472823"])
        assert("Zenodo ID must be prefixed by 'zenodo'" in str(e.exception))

    @mock.patch('requests.get', side_effect=mock_get)
    def test_pull_not_found(self, mock_get):
        with self.assertRaises(ZenodoError) as e:
            bosh(["pull", "zenodo.99999"])
        self.assertIn("Descriptor \"{0}\" not found".format("99999"),
                      str(e.exception))
