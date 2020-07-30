#!/usr/bin/env python

from boutiques import __file__ as bfile
from boutiques.bosh import bosh
from unittest import TestCase, skipIf
from boutiques_mocks import *
from boutiques.nexusHelper import NexusError
from boutiques.puller import ZenodoError
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord,\
    example_boutiques_tool
import sys
import os
import mock
import shutil
import pytest
import boutiques
import tempfile
import json
from urllib.request import urlretrieve


def setup():
    src = os.path.join(get_tests_dir(), "input-dir", "test-data-cache")
    shutil.copytree(src, mock_get_data_cache())


def cleanup():
    if os.path.isdir(mock_get_data_cache()):
        shutil.rmtree(mock_get_data_cache())


def get_tests_dir():
    return os.path.join(os.path.dirname(bfile), "tests")


def mock_get_data_cache():
    return os.path.join(os.path.dirname(bfile), "tests", "test-data-cache")


def mock_get_data_cache_file():
    return os.path.join(
        os.path.dirname(bfile), "tests", "test-data-cache", "nexus")


def mock_get_publish_single():
    return ([mock_zenodo_test_api_fail(),
             mock_zenodo_test_api(),
             mock_zenodo_test_api_fail(),
             mock_zenodo_test_api(),
             mock_zenodo_test_api_fail(),
             mock_zenodo_test_api(),
             mock_zenodo_test_api_fail(),
             mock_zenodo_test_api()])


def mock_post_publish_single():
    return([mock_zenodo_deposit(1234567),
            mock_zenodo_upload_descriptor(),
            mock_zenodo_publish(1234567),
            mock_zenodo_deposit(1234567),
            mock_zenodo_upload_descriptor(),
            mock_zenodo_publish(1234567)])


def mock_get_publish_bulk():
    return ([mock_zenodo_test_api_fail(),
             mock_zenodo_test_api()])


def mock_post_publish_bulk():
    return ([mock_zenodo_deposit(1234567),
             mock_zenodo_upload_descriptor(),
             mock_zenodo_upload_descriptor(),
             mock_zenodo_publish(1234567)])


def mock_get_publish_individual():
    return ([mock_zenodo_test_api_fail(),
             mock_zenodo_test_api()])


def mock_post_publish_individual():
    return ([mock_zenodo_deposit(1234567),
             mock_zenodo_upload_descriptor(),
             mock_zenodo_publish(1234567),
             mock_zenodo_deposit(2345678),
             mock_zenodo_upload_descriptor(),
             mock_zenodo_publish(2345678)])


def mock_get_invalid_nexus_endpoint():
    return "https://invalid.nexus.endpoint/v1"


def mock_get_empty_nexus_credentials():
    return {}


def mock_empty_function():
    return


def mock_get(query, *args, **kwargs):
    max_results = 5

    # Long description text to test truncation
    long_description = ("Lorem ipsum dolor sit amet, consectetur adipiscing "
                        "elit, sed do eiusmod tempor incididunt ut labore et "
                        "dolore magna aliqua. Ut enim ad minim veniam, quis "
                        "nostrud exercitation ullamco laboris nisi ut aliquip "
                        "ex ea commodo consequat.")

    mock_records = []
    # Return an arbitrary list of results with length max_results
    if query == "boutiques":
        for i in range(0, int(max_results)):
            mock_records.append(MockZenodoRecord(i, "Example Tool %s" % i,
                                                 long_description,
                                                 "exampleTool%s.json" % i, i))
    # Return only records containing the query
    else:
        mock_records.append(MockZenodoRecord(1234567, query))

    return mock_zenodo_search(mock_records)


def mock_urlretrieve(*args, **kwargs):
    mock_record1 = MockZenodoRecord(
        2636983, "fsl_bet-2019-04-11T215451.747382.json_foo", "",
        "https://zenodo.org/api/files/"
        "aae134af-9b9b-4613-b7b9-d5c5adcc7e61/"
        "fsl_bet-2019-04-11T215451.747382.json")
    mock_record2 = MockZenodoRecord(
        2636975, "MCFLIRT_2019-10-18T141903.880238_foo", "",
        "https://zenodo.org/api/files/"
        "151ef721-9f86-49bd-ae3d-045ae1766ee8/"
        "MCFLIRT-2019-04-11T213108.473348.json")
    temp = tempfile.NamedTemporaryFile(delete=False, mode='w+t')
    if "2636983" in args[0]:
        json.dump(mock_zenodo_search([mock_record1]).mock_json, temp)
        temp.close()
        return mock_zenodo_search([mock_record1])
    elif "2636975" in args[0]:
        json.dump(mock_zenodo_search([mock_record2]).mock_json, temp)
        temp.close()
        return mock_zenodo_search([mock_record2])
    else:
        return mock_zenodo_search([])


class TestDataHandler(TestCase):

    @mock.patch('requests.get')
    def test_search_all(self, mymockget):
        mymockget.side_effect = lambda *args, **kwargs: \
            mock_get("", False, *args, **kwargs)
        results = bosh(["data", "search"])
        self.assertGreater(len(results), 0)
        self.assertEqual(list(results[0].keys()),
                         ["ID", "TITLE", "DESCRIPTION",
                          "DOWNLOADS"])

    @mock.patch('requests.get')
    def test_search_verbose(self, mymockget):
        mymockget.side_effect = lambda *args, **kwargs: \
            mock_get("", False, *args, **kwargs)
        results = bosh(["data", "search", "-v"])
        self.assertGreater(len(results), 0)
        self.assertEqual(list(results[0].keys()),
                         ["ID", "TITLE", "DESCRIPTION", "PUBLICATION DATE",
                          "DEPRECATED", "DOWNLOADS", "AUTHOR",
                          "DOI", "CONTAINER", "TAGS"])

    @mock.patch('requests.get')
    def test_search_sorts_by_num_downloads(self, mymockget):
        mymockget.side_effect = lambda *args, **kwargs:\
            mock_get("boutiques",  *args, **kwargs)
        results = bosh(["data", "search"])
        downloads = []
        for r in results:
            downloads.append(r["DOWNLOADS"])
        self.assertEqual(sorted(downloads, reverse=True), downloads)

    @mock.patch('requests.get', side_effect=mock_urlretrieve)
    def test_pull(self, mock_urlretrieve):
        bosh(["data", "pull", "zenodo." + "2636975"])
        cache_dir = os.path.join(
            os.path.expanduser('~'), ".cache", "boutiques", "production")
        self.assertTrue(os.path.exists(os.path.join(
            cache_dir, "zenodo." + "2636975")))

    @mock.patch('requests.get', side_effect=mock_urlretrieve)
    def test_pull_multi(self, mock_urlretrieve):
        results = bosh(["data", "pull", "zenodo.2636983", "zenodo.2636975"])
        cache_dir = os.path.join(os.path.expanduser('~'),
                                 ".cache", "boutiques", "production")
        self.assertTrue(os.path.exists(os.path.join(
            cache_dir, "zenodo." + "2636983")))
        self.assertTrue(os.path.exists(os.path.join(cache_dir,
                                                    "zenodo.2636975")))
        self.assertEqual(len(results), 2, results)

    @mock.patch('requests.get', side_effect=mock_urlretrieve)
    def test_pull_duplicate_collapses(self, mock_urlretrieve):
        results = bosh(["data", "pull", "zenodo.2636983", "zenodo.2636975",
                        "zenodo.2636975"])
        self.assertEqual(len(results), 2, results)

    @mock.patch('requests.get', side_effect=mock_urlretrieve)
    def test_pull_missing_raises_exception(self, mock_urlretrieve):
        good1 = "zenodo.2636983"
        good2 = "zenodo.2636975"
        bad1 = "zenodo.9999990"
        with self.assertRaises(ZenodoError) as e:
            bosh(["data", "pull", good1, good2, bad1])
        self.assertIn("Execution record \"{0}\" not found".format(
            bad1.split(".")[1]),
            str(e.exception))

    @mock.patch('requests.get', side_effect=mock_urlretrieve)
    def test_pull_missing_prefix(self, mock_urlretrieve):
        with self.assertRaises(ZenodoError) as e:
            bosh(["data", "pull", "2636983"])
        self.assertIn("Zenodo ID must be prefixed by 'zenodo'",
                      str(e.exception))

    def test_pull_not_found(self):
        with self.assertRaises(ZenodoError) as e:
            bosh(["data", "pull", "zenodo.99999"])
        self.assertIn("Execution record \"{0}\" not found".format("99999"),
                      str(e.exception))

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    def test_inspect(self, mock_dir):
        cleanup()
        setup()

        boutiques.data("inspect")
        out, _ = self.capfd.readouterr()
        self.assertIn("There are 3 unpublished records in the cache", out)

        boutiques.data("inspect", "-e")
        out, _ = self.capfd.readouterr()
        self.assertIn("summary", out)
        self.assertIn("descriptor-doi", out)

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    def test_delete(self, mock_dir):
        cleanup()
        setup()

        with self.assertRaises(ValueError) as e:
            bosh(["data", "delete", "-f", "bad-filename", "--no-int"])
        self.assertIn("File bad-filename does not exist in the data cache",
                      str(e.exception))

        fl1_path = os.path.join(mock_get_data_cache(), "tool1_123.json")
        fl2_path = os.path.join(mock_get_data_cache(), "tool2_123.json")
        bosh(["data", "delete", "-f", "tool1_123.json", "-y"])
        self.assertFalse(os.path.isfile(fl1_path))
        bosh(["data", "delete", "-f", fl2_path, "-y"])
        self.assertFalse(os.path.isfile(fl2_path))
        bosh(["data", "delete", "-y"])
        self.assertEqual(len(os.listdir(mock_get_data_cache())), 0)

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    @mock.patch('requests.get', side_effect=mock_get_publish_single())
    @mock.patch('requests.post', side_effect=mock_post_publish_single())
    def test_publish_single(self, mock_dir, mock_get, mock_post):
        cleanup()
        setup()

        # Publish a record that does not exist
        with self.assertRaises(ValueError) as e:
            bosh(["data", "publish", "-f", "bad-filename", "--sandbox", "-y"])
        self.assertIn("File bad-filename does not exist in the data cache",
                      str(e.exception))

        # Publish a record with a correct descriptor-doi
        bosh(["data", "publish", "-f", "tool1_123.json", "-y",
              "--sandbox", "--zenodo-token",
              "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertFalse(os.path.isfile(
            os.path.join(mock_get_data_cache(), "tool1-123")))

        # Publish a record without a descriptor-doi
        bosh(["data", "publish", "-f", "tool2_123.json", "-y",
              "--sandbox", "--zenodo-token",
              "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue(os.path.isfile(
            os.path.join(mock_get_data_cache(), "tool2_123.json")))
        self.assertTrue(os.path.isfile(
            os.path.join(mock_get_data_cache(), "descriptor_tool2_123.json")))

        # Publish a record without a descriptor-doi but descriptor is published
        bosh(["data", "publish", "-f", "tool3_123.json", "-y",
              "--sandbox", "--zenodo-token",
              "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertFalse(os.path.isfile(
            os.path.join(mock_get_data_cache(), "tool3-123")))
        self.assertFalse(os.path.isfile(
            os.path.join(mock_get_data_cache(), "descriptor-tool3-123")))

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    @mock.patch('requests.get', side_effect=mock_get_publish_bulk())
    @mock.patch('requests.post', side_effect=mock_post_publish_bulk())
    def test_publish_bulk(self, mock_dir, mock_get, mock_post):
        cleanup()
        setup()

        bosh(["data", "publish", "-y", "--sandbox", "--zenodo-token",
              "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertEqual(len(os.listdir(os.path.join(mock_get_data_cache()))),
                         2)

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    @mock.patch('requests.get', side_effect=mock_get_publish_individual())
    @mock.patch('requests.post', side_effect=mock_post_publish_individual())
    def test_publish_individual(self, mock_dir, mock_get, mock_post):
        cleanup()
        setup()

        bosh(["data", "publish", "-y", "--individual",
              "--sandbox", "--zenodo-token",
              "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertEqual(len(os.listdir(os.path.join(mock_get_data_cache()))),
                         2)

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    @mock.patch('boutiques.nexusHelper.NexusHelper.read_credentials',
                return_value=mock_get_empty_nexus_credentials())
    def test_publish_nexus_no_token_fail(self, mock_dir, mock_cred):
        cleanup()
        setup()

        with self.assertRaises(NexusError) as e:
            bosh(["data", "publish", "-y", "--nexus", "--sandbox"])
        self.assertIn("Cannot find Nexus credentials.",
                      str(e.exception))

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    @mock.patch('boutiques.nexusHelper.NexusHelper.read_credentials',
                return_value=mock_get_empty_nexus_credentials())
    def test_publish_nexus_no_organization_fail(self, mock_dir, mock_cred):
        cleanup()
        setup()

        with self.assertRaises(NexusError) as e:
            bosh(["data", "publish", "-y", "--nexus", "--sandbox",
                  "--nexus-token", "hAaW2wSBZMskxpfigTYHcuDrCPWr2"])
        self.assertIn("Cannot find Nexus organization.",
                      str(e.exception))

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    @mock.patch('boutiques.nexusHelper.NexusHelper.read_credentials',
                return_value=mock_get_empty_nexus_credentials())
    def test_publish_nexus_no_project_fail(self, mock_dir, mock_cred):
        cleanup()
        setup()

        with self.assertRaises(NexusError) as e:
            bosh(["data", "publish", "-y", "--nexus", "--sandbox",
                  "--nexus-token", "hAaW2wSBZMskxpfigTYHcuDrCPWr2",
                  "--nexus-org", "boutiques"])
        self.assertIn("Cannot find Nexus project.",
                      str(e.exception))

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    @mock.patch('boutiques.nexusHelper.NexusHelper.get_nexus_endpoint',
                return_value=mock_get_invalid_nexus_endpoint())
    def test_publish_nexus_invalid_endpoint(self, mock_dir, mock_endpoint):
        cleanup()
        setup()

        with self.assertRaises(NexusError) as e:
            bosh(["data", "publish", "-y", "--nexus", "--sandbox",
                  "--nexus-token", "hAaW2wSBZMskxpfigTYHcuDrCPWr2",
                  "--nexus-org", "boutiques", "--nexus-project",
                  "test"])
        self.assertIn("Cannot access Nexus endpoint",
                      str(e.exception))

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    def test_publish_nexus_invalid_token(self, mock_dir):
        cleanup()
        setup()

        with self.assertRaises(NexusError) as e:
            bosh(["data", "publish", "-y", "--nexus", "--sandbox",
                  "--nexus-token", "INVALIDTOKEN",
                  "--nexus-org", "boutiques", "--nexus-project",
                  "test"])
        self.assertIn("Cannot authenticate to Nexus API, check "
                      "your access token", str(e.exception))

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    @mock.patch('boutiques.nexusHelper.NexusHelper.get_config_file',
                return_value=mock_get_data_cache_file())
    @mock.patch('boutiques.nexusHelper.NexusHelper.nexus_test_api',
                return_value=mock_empty_function())
    @mock.patch('nexussdk.files.create',
                return_value=mock_empty_function())
    def test_publish_nexus_success(
            self, mock_create_file, mock_fetch_project,
            mock_save_inputs, mock_dir):
        cleanup()
        setup()

        try:
            bosh(["data", "publish", "-y", "--nexus", "--sandbox",
                  "--nexus-token", "hAaW2wSBZMskxpfigTYHcuDrCPWr2",
                  "--nexus-org", "test", "--nexus-project",
                  "test", "-v"])
        except Exception as e:
            self.fail("Unexpected exception raised: " + str(e))

    # Captures the stdout and stderr during test execution
    # and returns them as a tuple in readouterr()
    @pytest.fixture(autouse=True)
    def capfd(self, capfd):
        self.capfd = capfd
