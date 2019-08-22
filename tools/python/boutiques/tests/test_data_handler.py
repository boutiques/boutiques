#!/usr/bin/env python

from boutiques import __file__ as bfile
from boutiques.bosh import bosh
from unittest import TestCase, skipIf
from boutiques_mocks import *
from boutiques.nexusHelper import NexusError
import sys
import os
import mock
import shutil
import pytest
import boutiques


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


class TestDataHandler(TestCase):

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

    @skipIf(sys.version_info < (3, 5),
            'Python version has to be >= 3.5')
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

    @skipIf(sys.version_info < (3, 5),
            'Python version has to be >= 3.5')
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

    @skipIf(sys.version_info < (3, 5),
            'Python version has to be >= 3.5')
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

    @skipIf(sys.version_info < (3, 5),
            'Python version has to be >= 3.5')
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

    @skipIf(sys.version_info < (3, 5),
            'Python version has to be >= 3.5')
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

    @skipIf(sys.version_info < (3, 5),
            'Python version has to be >= 3.5')
    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    @mock.patch('boutiques.nexusHelper.NexusHelper.save_nexus_inputs',
                return_value=mock_empty_function())
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
                  "test"])
        except Exception as e:
            self.fail("Unexpected exception raised: " + str(e))

    # Captures the stdout and stderr during test execution
    # and returns them as a tuple in readouterr()
    @pytest.fixture(autouse=True)
    def capfd(self, capfd):
        self.capfd = capfd
