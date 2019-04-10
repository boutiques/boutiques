#!/usr/bin/env python

from boutiques import __file__ as bfile
from boutiques.bosh import bosh
from unittest import TestCase
from boutiques.dataHandler import ZenodoError, getDataCacheDir
import os
import mock
import shutil

def test_setup():
    src = os.path.join(get_tests_dir(), "input-dir", "test-data-cache")
    shutil.copytree(src, get_tests_dir())

def cleanup():
    shutil.rmtree(mock_get_data_cache())

def get_tests_dir():
    return os.path.join(os.path.dirname(bfile), "tests")


def mock_get_data_cache():
    return os.path.join(os.path.dirname(bfile), "tests", "test-data-cache")

class TestDataHandler(TestCase):

    @mock.patch('dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    def test_inspect(self, mock_dir):
        test_setup()

        output = bosh(["data", "inspect", "-e"])
        output = bosh(["data", "inspect"])

        cleanup()

    @mock.patch('dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    def test_discard(self, mock_dir):
        test_setup()

        with self.assertRaises(ValueError) as e:
            bosh(["data", "delete", "-f", "bad-filename"])
        self.assertIn("File bad-filename does not exist in the data cache",
                      str(e.exception))

        fl1_path = os.path.join(mock_get_data_cache(), "test-301")
        fl2_path = os.path.join(mock_get_data_cache(), "example-2019")
        result = bosh(["data", "delete", "-f", "test-301"])
        self.assertFalse(os.path.isfile(fl1_path))
        result = bosh(["data", "delete", "-f", fl2_path])
        self.assertFalse(os.path.isfile(fl2_path))

        with self.assertRaises(ValueError) as e:
            bosh(["data", "delete"])
        self.assertIn("Must indicate a file to discard", str(e.exception))

        result = bosh(["data", "delete", "-a"])
        self.assertEqual(len(os.listdir(mock_get_data_cache())), 0)

        cleanup()

    @mock.patch('dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    def test_publish_single(self, mock_dir):
        # test_setup()
        #
        # # Publish a record that does not exist
        # with self.assertRaises(ValueError) as e:
        #     bosh(["data", "publish", "-f", "bad-filename", "--sandbox", "-y"])
        # self.assertIn("file bad-fliename does not exist in the data cache",
        #               str(e.exception))
        #
        # # Publish a record with a correct descriptor-doi
        # bosh(["data", "publish", "-f", "tool1-123", "-y",
        #       "--sandbox", "--zenodo-token",
        #       "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        # self.assertFalse(os.path.isfile(
        #     os.path.join(mock_get_data_cache(), "tool1-123")))
        #
        # # Publish a record without a descriptor-doi
        # bosh(["data", "publish", "-f", "tool2-123", "-y",
        #       "--sandbox", "--zenodo-token",
        #       "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        # self.assertTrue(os.path.isfile(
        #     os.path.join(mock_get_data_cache(), "tool2-123")))
        # self.assertTrue(os.path.isfile(
        #     os.path.join(mock_get_data_cache(), "descriptor-tool2-123")))
        #
        # # Publish a record without a descriptor-doi but descriptor is published
        # bosh(["data", "publish", "-f", "tool3-123.json", "-y",
        #       "--sandbox", "--zenodo-token",
        #       "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        # self.assertFalse(os.path.isfile(
        #     os.path.join(mock_get_data_cache(), "tool3-123")))
        # self.assertFalse(os.path.isfile(
        #     os.path.join(mock_get_data_cache(), "descriptor-tool3-123")))
        #
        # cleanup()

    @mock.patch('dataHandler.getDataCacheDir',
                return_value=mock_get_data_cache())
    def test_publish_bulk(self, mock_dir):
        # test_setup()
        #
        # bosh(["data", "publish", "-y",
        #       "--sandbox", "--zenodo-token",
        #       "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        # self.assertEqual(os.listdir(os.path.join(mock_get_data_cache())), 2)
        #
        # cleanup()