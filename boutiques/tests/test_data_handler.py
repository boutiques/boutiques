#!/usr/bin/env python

import os
import shutil
from unittest import mock

import pytest
from boutiques_mocks import (
    mock_empty_function,
    mock_get_data_cache,
    mock_get_data_cache_file,
    mock_get_empty_nexus_credentials,
    mock_get_invalid_nexus_endpoint,
    mock_get_publish_bulk,
    mock_get_publish_single,
    mock_post_publish_bulk,
    mock_post_publish_single,
)

import boutiques
from boutiques.bosh import bosh
from boutiques.nexusHelper import NexusError
from boutiques.tests.BaseTest import BaseTest


class TestDataHandler(BaseTest):
    @pytest.fixture(autouse=True)
    def reset(self):
        # Reset before each test
        if os.path.isdir(mock_get_data_cache()):
            shutil.rmtree(mock_get_data_cache())
        src = self.get_file_path("data_collection/input_dir/test-data-cache")
        shutil.copytree(src, mock_get_data_cache())

    # Captures the stdout and stderr during test execution
    # and returns them as a tuple in readouterr()
    @pytest.fixture(autouse=True)
    def capture_st(self, capfd):
        self.capfd = capfd

    @mock.patch(
        "boutiques.dataHandler.getDataCacheDir",
        return_value=mock_get_data_cache(),
    )
    def test_inspect(self, mock_dir):
        boutiques.data("inspect")
        out, _ = self.capfd.readouterr()
        self.assertIn("There are 3 unpublished records in the cache", out)

        boutiques.data("inspect", "-e")
        out, _ = self.capfd.readouterr()
        self.assertIn("summary", out)
        self.assertIn("descriptor-doi", out)

    @mock.patch(
        "boutiques.dataHandler.getDataCacheDir",
        return_value=mock_get_data_cache(),
    )
    def test_delete(self, mock_dir):
        with self.assertRaises(ValueError) as e:
            bosh(["data", "delete", "-f", "bad-filename", "--no-int"])
        self.assertIn(
            "File bad-filename does not exist in the data cache",
            str(e.exception),
        )

        fl1_path = os.path.join(mock_get_data_cache(), "tool1_123.json")
        fl2_path = os.path.join(mock_get_data_cache(), "tool2_123.json")
        bosh(["data", "delete", "-f", "tool1_123.json", "-y"])
        self.assertFalse(os.path.isfile(fl1_path))
        bosh(["data", "delete", "-f", fl2_path, "-y"])
        self.assertFalse(os.path.isfile(fl2_path))
        bosh(["data", "delete", "-y"])
        self.assertEqual(len(os.listdir(mock_get_data_cache())), 0)

    @mock.patch(
        "boutiques.dataHandler.getDataCacheDir",
        return_value=mock_get_data_cache(),
    )
    @mock.patch("requests.get", side_effect=mock_get_publish_single())
    @mock.patch("requests.post", side_effect=mock_post_publish_single())
    def test_publish_single(self, mock_dir, mock_get, mock_post):
        # Publish a record that does not exist
        with self.assertRaises(ValueError) as e:
            bosh(["data", "publish", "-f", "bad-filename", "--sandbox", "-y"])
        self.assertIn(
            "File bad-filename does not exist in the data cache",
            str(e.exception),
        )

        # Publish a record with a correct descriptor-doi
        bosh(
            [
                "data",
                "publish",
                "-f",
                "tool1_123.json",
                "-y",
                "--sandbox",
                "--zenodo-token",
                "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r",
            ]
        )
        self.assertFalse(
            os.path.isfile(os.path.join(mock_get_data_cache(), "tool1-123"))
        )

        # Publish a record without a descriptor-doi
        bosh(
            [
                "data",
                "publish",
                "-f",
                "tool2_123.json",
                "-y",
                "--sandbox",
                "--zenodo-token",
                "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r",
            ]
        )
        self.assertTrue(
            os.path.isfile(
                os.path.join(mock_get_data_cache(), "tool2_123.json")
            )
        )
        self.assertTrue(
            os.path.isfile(
                os.path.join(mock_get_data_cache(), "descriptor_tool2_123.json")
            )
        )

        # Publish a record without a descriptor-doi but descriptor is published
        bosh(
            [
                "data",
                "publish",
                "-f",
                "tool3_123.json",
                "-y",
                "--sandbox",
                "--zenodo-token",
                "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r",
            ]
        )
        self.assertFalse(
            os.path.isfile(os.path.join(mock_get_data_cache(), "tool3-123"))
        )
        self.assertFalse(
            os.path.isfile(
                os.path.join(mock_get_data_cache(), "descriptor-tool3-123")
            )
        )

    @mock.patch(
        "boutiques.dataHandler.getDataCacheDir",
        return_value=mock_get_data_cache(),
    )
    @mock.patch("requests.get", side_effect=mock_get_publish_bulk())
    @mock.patch("requests.post", side_effect=mock_post_publish_bulk())
    def test_publish_bulk(self, mock_dir, mock_get, mock_post):
        bosh(
            [
                "data",
                "publish",
                "-y",
                "--sandbox",
                "--zenodo-token",
                "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r",
            ]
        )
        self.assertEqual(
            len(os.listdir(os.path.join(mock_get_data_cache()))), 2
        )

    @mock.patch(
        "boutiques.dataHandler.getDataCacheDir",
        return_value=mock_get_data_cache(),
    )
    @mock.patch("requests.get", side_effect=mock_get_publish_single())
    @mock.patch("requests.post", side_effect=mock_post_publish_single())
    def test_publish_individual(self, mock_dir, mock_get, mock_post):
        bosh(
            [
                "data",
                "publish",
                "-y",
                "--individual",
                "--sandbox",
                "--zenodo-token",
                "hAaW2wSBZMskxpfigTYHcuDrCPWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r",
            ]
        )
        self.assertEqual(
            len(os.listdir(os.path.join(mock_get_data_cache()))), 2
        )

    @mock.patch(
        "boutiques.dataHandler.getDataCacheDir",
        return_value=mock_get_data_cache(),
    )
    @mock.patch(
        "boutiques.nexusHelper.NexusHelper.read_credentials",
        return_value=mock_get_empty_nexus_credentials(),
    )
    def test_publish_nexus_no_token_fail(self, mock_dir, mock_cred):
        with self.assertRaises(NexusError) as e:
            bosh(["data", "publish", "-y", "--nexus", "--sandbox"])
        self.assertIn("Cannot find Nexus credentials.", str(e.exception))

    @mock.patch(
        "boutiques.dataHandler.getDataCacheDir",
        return_value=mock_get_data_cache(),
    )
    @mock.patch(
        "boutiques.nexusHelper.NexusHelper.read_credentials",
        return_value=mock_get_empty_nexus_credentials(),
    )
    def test_publish_nexus_no_organization_fail(self, mock_dir, mock_cred):
        with self.assertRaises(NexusError) as e:
            bosh(
                [
                    "data",
                    "publish",
                    "-y",
                    "--nexus",
                    "--sandbox",
                    "--nexus-token",
                    "hAaW2wSBZMskxpfigTYHcuDrCPWr2",
                ]
            )
        self.assertIn("Cannot find Nexus organization.", str(e.exception))

    @mock.patch(
        "boutiques.dataHandler.getDataCacheDir",
        return_value=mock_get_data_cache(),
    )
    @mock.patch(
        "boutiques.nexusHelper.NexusHelper.read_credentials",
        return_value=mock_get_empty_nexus_credentials(),
    )
    def test_publish_nexus_no_project_fail(self, mock_dir, mock_cred):
        with self.assertRaises(NexusError) as e:
            bosh(
                [
                    "data",
                    "publish",
                    "-y",
                    "--nexus",
                    "--sandbox",
                    "--nexus-token",
                    "hAaW2wSBZMskxpfigTYHcuDrCPWr2",
                    "--nexus-org",
                    "boutiques",
                ]
            )
        self.assertIn("Cannot find Nexus project.", str(e.exception))

    @mock.patch(
        "boutiques.dataHandler.getDataCacheDir",
        return_value=mock_get_data_cache(),
    )
    @mock.patch(
        "boutiques.nexusHelper.NexusHelper.get_nexus_endpoint",
        return_value=mock_get_invalid_nexus_endpoint(),
    )
    def test_publish_nexus_invalid_endpoint(self, mock_dir, mock_endpoint):
        with self.assertRaises(NexusError) as e:
            bosh(
                [
                    "data",
                    "publish",
                    "-y",
                    "--nexus",
                    "--sandbox",
                    "--nexus-token",
                    "hAaW2wSBZMskxpfigTYHcuDrCPWr2",
                    "--nexus-org",
                    "boutiques",
                    "--nexus-project",
                    "test",
                ]
            )
        self.assertIn("Cannot access Nexus endpoint", str(e.exception))

    @mock.patch(
        "boutiques.dataHandler.getDataCacheDir",
        return_value=mock_get_data_cache(),
    )
    def test_publish_nexus_invalid_token(self, mock_dir):
        with self.assertRaises(NexusError) as e:
            bosh(
                [
                    "data",
                    "publish",
                    "-y",
                    "--nexus",
                    "--sandbox",
                    "--nexus-token",
                    "INVALIDTOKEN",
                    "--nexus-org",
                    "boutiques",
                    "--nexus-project",
                    "test",
                ]
            )
        self.assertIn(
            "Cannot authenticate to Nexus API, check " "your access token",
            str(e.exception),
        )

    @mock.patch(
        "boutiques.dataHandler.getDataCacheDir",
        return_value=mock_get_data_cache(),
    )
    @mock.patch(
        "boutiques.nexusHelper.NexusHelper.get_config_file",
        return_value=mock_get_data_cache_file(),
    )
    @mock.patch(
        "boutiques.nexusHelper.NexusHelper.nexus_test_api",
        return_value=mock_empty_function(),
    )
    @mock.patch("nexussdk.files.create", return_value=mock_empty_function())
    def test_publish_nexus_success(
        self, mock_create_file, mock_fetch_project, mock_save_inputs, mock_dir
    ):
        try:
            bosh(
                [
                    "data",
                    "publish",
                    "-y",
                    "--nexus",
                    "--sandbox",
                    "--nexus-token",
                    "hAaW2wSBZMskxpfigTYHcuDrCPWr2",
                    "--nexus-org",
                    "test",
                    "--nexus-project",
                    "test",
                    "-v",
                ]
            )
        except Exception as e:
            self.fail("Unexpected exception raised: " + str(e))
