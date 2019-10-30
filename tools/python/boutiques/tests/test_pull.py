from boutiques.bosh import bosh
from unittest import TestCase
from boutiques.puller import ZenodoError
import os
import mock
import tempfile
import json

from boutiques_mocks import mock_zenodo_search, MockZenodoRecord,\
    example_boutiques_tool

try:
    # Python 3
    from urllib.request import urlopen
    from urllib.request import urlretrieve
except ImportError:
    # Python 2
    from urllib2 import urlopen
    from urllib import urlretrieve


def mock_urlretrieve(*args, **kwargs):
    mock_record1 = example_boutiques_tool
    mock_record2 = MockZenodoRecord(2587160, "makeblastdb_foo", "",
                                    "https://zenodo.org/api/files/"
                                    "d861b2cd-ec68-4613-9847-1911904a1218/"
                                    "makeblastdb.json")
    temp = tempfile.NamedTemporaryFile(delete=False)
    if str(example_boutiques_tool.id) in args[0]:
        json.dump(mock_zenodo_search([mock_record1]).mock_json, temp)
        temp.close()
        return urlretrieve(temp.name, args[1])
    if "makeblastdb.json" in args[0]:
        json.dump(mock_zenodo_search([mock_record2]).mock_json, temp)
        temp.close()
        return urlretrieve(temp.name, args[1])
    return urlretrieve(args[0], args[1])


class TestPull(TestCase):

    @mock.patch('boutiques.puller.urlretrieve', side_effect=mock_urlretrieve)
    def test_pull(self, mock_urlretrieve):
        bosh(["pull", "zenodo." + str(example_boutiques_tool.id)])
        cache_dir = os.path.join(os.path.expanduser('~'), ".cache", "boutiques")
        self.assertTrue(os.path.exists(os.path.join(
            cache_dir, "zenodo-" + str(example_boutiques_tool.id) + ".json")))

    @mock.patch('boutiques.puller.urlretrieve', side_effect=mock_urlretrieve)
    def test_pull_multi(self, mock_urlretrieve):
        results = bosh(["pull", "zenodo." +
                        str(example_boutiques_tool.id), "zenodo.2587160"])
        cache_dir = os.path.join(os.path.expanduser('~'), ".cache", "boutiques")
        self.assertTrue(os.path.exists(os.path.join(
            cache_dir, "zenodo-" + str(example_boutiques_tool.id) + ".json")))
        self.assertTrue(os.path.exists(os.path.join(cache_dir,
                                                    "zenodo-2587160.json")))
        self.assertEqual(len(results), 2, results)

    @mock.patch('boutiques.puller.urlretrieve', side_effect=mock_urlretrieve)
    def test_pull_duplicate_collapses(self, mock_urlretrieve):
        results = bosh(["pull", "zenodo." +
                        str(example_boutiques_tool.id), "zenodo.2587160",
                        "zenodo.2587160"])
        self.assertEqual(len(results), 2, results)

    @mock.patch('boutiques.puller.urlretrieve', side_effect=mock_urlretrieve)
    def test_pull_missing_raises_exception(self, mock_urlretrieve):
        good1 = "zenodo." + str(example_boutiques_tool.id)
        good2 = "zenodo.2587160"
        bad1 = "zenodo.9999990"
        with self.assertRaises(ZenodoError) as e:
            bosh(["pull", good1, bad1, good2])
        self.assertIn("Descriptor \"{0}\" not found".format(
            bad1.split(".")[1]),
            str(e.exception))

    @mock.patch('boutiques.puller.urlretrieve', side_effect=mock_urlretrieve)
    def test_pull_missing_prefix(self, mock_urlretrieve):
        with self.assertRaises(ZenodoError) as e:
            bosh(["pull", str(example_boutiques_tool.id)])
        self.assertIn("Zenodo ID must be prefixed by 'zenodo'",
                      str(e.exception))

    @mock.patch('boutiques.puller.urlretrieve', side_effect=mock_urlretrieve)
    def test_pull_not_found(self, mock_urlretrieve):
        with self.assertRaises(ZenodoError) as e:
            bosh(["pull", "zenodo.99999"])
        self.assertIn("Descriptor \"{0}\" not found".format("99999"),
                      str(e.exception))
