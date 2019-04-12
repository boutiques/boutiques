#!/usr/bin/env python

from boutiques import __file__ as bfile
from boutiques.bosh import bosh
from unittest import TestCase
from boutiques_mocks import *
import os
import mock
import shutil


def setup():
    src = os.path.join(get_tests_dir(), "input-dir", "test-data-cache")
    shutil.copytree(src, os.path.join(get_tests_dir(), "test-data-cache"))


def cleanup():
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
    return([mock_zenodo_deposit(1234567),
            mock_zenodo_upload_descriptor(),
            mock_zenodo_upload_descriptor(),
            mock_zenodo_publish(1234567)])

def mock_get_publish_individual():
  return ([mock_zenodo_test_api_fail(),
           mock_zenodo_test_api()])


def mock_post_publish_individual():
  return([mock_zenodo_deposit(1234567),
          mock_zenodo_upload_descriptor(),
          mock_zenodo_publish(1234567),
          mock_zenodo_deposit(2345678),
          mock_zenodo_upload_descriptor(),
          mock_zenodo_publish(2345678)])


class TestDataHandler(TestCase):

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    def test_inspect(self, mock_dir):
        setup()

        bosh(["data", "inspect", "-e"])
        bosh(["data", "inspect"])

        cleanup()

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    def test_delete(self, mock_dir):
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

        cleanup()

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    @mock.patch('requests.get', side_effect=mock_get_publish_single())
    @mock.patch('requests.post', side_effect=mock_post_publish_single())
    def test_publish_single(self, mock_dir, mock_get, mock_post):
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

        cleanup()

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    @mock.patch('requests.get', side_effect=mock_get_publish_bulk())
    @mock.patch('requests.post', side_effect=mock_post_publish_bulk())
    def test_publish_bulk(self, mock_dir, mock_get, mock_post):
        setup()

        bosh(["data", "publish", "-y", "--sandbox", "--zenodo-token",
              "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertEqual(len(os.listdir(os.path.join(mock_get_data_cache()))),
                         2)

        cleanup()

    @mock.patch('boutiques.dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    @mock.patch('requests.get', side_effect=mock_get_publish_individual())
    @mock.patch('requests.post', side_effect=mock_post_publish_individual())
    def test_publish_individual(self, mock_dir, mock_get, mock_post):
      setup()

      bosh(["data", "publish", "-y", "--individual",
            "--sandbox", "--zenodo-token",
            "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
      self.assertEqual(len(os.listdir(os.path.join(mock_get_data_cache()))),
                       2)

      cleanup()
