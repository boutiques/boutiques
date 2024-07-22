import os.path as op
import shutil
import subprocess
import tempfile
from collections import OrderedDict

import mock
import pytest
import simplejson as json
from boutiques_mocks import (
    MockHttpResponse,
    MockZenodoRecord,
    mock_get_publish_bulk,
    mock_zenodo_delete_files,
    mock_zenodo_deposit,
    mock_zenodo_no_permission,
    mock_zenodo_publish,
    mock_zenodo_search,
    mock_zenodo_test_api,
    mock_zenodo_test_api_fail,
    mock_zenodo_upload_descriptor,
)

from boutiques.bosh import bosh
from boutiques.publisher import ZenodoError
from boutiques.tests.BaseTest import BaseTest


def mock_zenodo_deposit_updated(old_zid, new_zid):
    mock_json = {
                  "links": {
                    "latest_draft": "https://zenodo.org/api/record/%s"
                                    % new_zid
                  },
                  "files": [
                    {
                      "id": 1234
                    }
                  ],
                  "doi": "10.5072/zenodo.%s"
                         % old_zid
                }
    return MockHttpResponse(201, mock_json)


def mock_get_publish_then_update():
    mock_record = MockZenodoRecord(1234567, "Example Boutiques Tool")
    return ([mock_zenodo_test_api_fail(),
            mock_zenodo_test_api(),
            mock_zenodo_search([]),
            mock_zenodo_test_api_fail(),
            mock_zenodo_test_api(),
            mock_zenodo_search([mock_record])])


def mock_post_publish_then_update():
    return ([mock_zenodo_deposit(1234567),
            mock_zenodo_upload_descriptor(),
            mock_zenodo_publish(1234567),
            mock_zenodo_deposit_updated(1234567, 2345678),
            mock_zenodo_upload_descriptor(),
            mock_zenodo_publish(2345678)])


def mock_post_publish_update_only():
    return ([mock_zenodo_deposit_updated(1234567, 2345678),
            mock_zenodo_upload_descriptor(),
            mock_zenodo_publish(2345678)])


class TestPublisher(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("publisher")

    @mock.patch('requests.get', side_effect=mock_get_publish_then_update())
    @mock.patch('requests.post', side_effect=mock_post_publish_then_update())
    @mock.patch('requests.put', return_value=mock_zenodo_test_api())
    @mock.patch('requests.delete', return_value=mock_zenodo_delete_files())
    def test_publication(self, mock_get, mock_post, mock_put, mock_delete):
        example1_desc = self.example1_descriptor
        temp_descriptor = tempfile.NamedTemporaryFile(suffix=".json")
        shutil.copyfile(example1_desc, temp_descriptor.name)

        # Make sure that example1.json doesn't have a DOI yet
        with open(temp_descriptor.name, 'r') as fhandle:
            descriptor = json.load(fhandle)
            self.assertIsNone(descriptor.get('doi'))

        # Test publication of a descriptor that doesn't have a DOI
        doi = bosh(["publish",
                    temp_descriptor.name,
                    "--sandbox", "-y", "-v",
                    "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                    "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue(doi)

        # Now descriptor should have a DOI
        with open(temp_descriptor.name, 'r') as fhandle:
            descriptor = json.load(fhandle)
            self.assertEqual(descriptor.get('doi'), doi)

        # Test publication of a descriptor that already has a DOI
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish",
                  temp_descriptor.name,
                  "--sandbox", "-y", "-v",
                  "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                  "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue("Descriptor already has a DOI" in str(e.exception))

        # Test publication of an updated version of the same descriptor
        example1_desc_updated = self.get_file_path(
            "example1_docker_updated.json")
        temp_descriptor_updated = tempfile.NamedTemporaryFile(suffix=".json")
        shutil.copyfile(example1_desc_updated, temp_descriptor_updated.name)

        # Publish the updated version
        new_doi = bosh(["publish",
                        temp_descriptor_updated.name,
                        "--sandbox", "-y", "-v",
                        "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                        "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue(new_doi)

        # Updated version of descriptor should have a new DOI
        with open(temp_descriptor_updated.name, 'r') as fhandle:
            descriptor_updated = json.load(fhandle)
            self.assertNotEqual(new_doi, doi)
            self.assertEqual(descriptor_updated.get('doi'), new_doi)

    @mock.patch('requests.get', return_value=mock_zenodo_test_api_fail())
    def test_publisher_auth(self, mock_get):
        test_desc = self.example1_descriptor
        # Bad token should fail
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish", test_desc, "--sandbox",
                  "-y", "-v", "--zenodo-token", "12345"])
        self.assertIn("Cannot authenticate to Zenodo", str(e.exception))

        # No token should fail
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish", test_desc, "--sandbox", "-y", "-v"])
        self.assertIn("Cannot authenticate to Zenodo", str(e.exception))

    # Note that this test does not use mocks as the mocks don't seem
    # to work with subprocess.Popen.
    def test_publisher_auth_fail_cli(self):
        command = ("bosh publish " +
                   self.example1_descriptor +
                   " --sandbox -y -v --zenodo-token 12345")
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate()
        self.assertTrue(process.returncode)

    @mock.patch('requests.get', side_effect=mock_get_publish_bulk())
    @mock.patch('requests.post', side_effect=mock_post_publish_update_only())
    @mock.patch('requests.put', return_value=mock_zenodo_test_api())
    @mock.patch('requests.delete', return_value=mock_zenodo_delete_files())
    def test_publication_replace_with_id(self, mock_get, mock_post, mock_put,
                                         mock_delete):
        example1_desc = self.example1_descriptor
        temp_descriptor = tempfile.NamedTemporaryFile(suffix=".json")
        shutil.copyfile(example1_desc, temp_descriptor.name)

        # Make sure that example1.json doesn't have a DOI yet
        with open(temp_descriptor.name, 'r') as fhandle:
            descriptor = json.load(fhandle)
            self.assertIsNone(descriptor.get('doi'))

        # Publish an updated version of an already published descriptor
        doi = bosh(["publish",
                    temp_descriptor.name,
                    "--sandbox", "-y", "-v",
                    "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                                      "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r",
                    "--id", "zenodo.1234567"])
        self.assertTrue(doi)

        # Now descriptor should have a DOI
        with open(temp_descriptor.name, 'r') as fhandle:
            descriptor = json.load(fhandle)
            self.assertEqual(descriptor.get('doi'), doi)

    def test_publication_errors(self):
        # Update an already published descriptor (wrong id)
        example1_desc = self.example1_descriptor
        temp_descriptor = tempfile.NamedTemporaryFile(suffix=".json")
        shutil.copyfile(example1_desc, temp_descriptor.name)
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish",
                  temp_descriptor.name,
                  "--sandbox", "-y", "-v",
                  "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                                    "PWr2VeQZgBLErKbfF5RdrKhzzJ"
                                    "i8i2hnN8r",
                  "--id", "this_is_a_wrong_id"])
        self.assertTrue("Zenodo ID must be prefixed by 'zenodo'"
                        in str(e.exception))

        # Publish a descriptor that doesn't have an author
        good_desc = op.join(self.tests_dir, "invocation", "good.json")
        temp_descriptor = tempfile.NamedTemporaryFile(suffix=".json")
        shutil.copyfile(good_desc, temp_descriptor.name)
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish",
                  temp_descriptor.name,
                  "--sandbox", "-y", "-v",
                  "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                                    "PWr2VeQZgBLErKbfF5RdrKhzzJ"
                                    "i8i2hnN8r"])
        self.assertTrue("Tool must have an author to be published."
                        in str(e.exception))

        # Publish a descriptor that doesn't have a container image
        good_desc = op.join(self.tests_dir, "exec", "no_container.json")
        temp_descriptor = tempfile.NamedTemporaryFile(suffix=".json")
        shutil.copyfile(good_desc, temp_descriptor.name)
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish",
                  temp_descriptor.name,
                  "--sandbox", "-y", "-v",
                  "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                                    "PWr2VeQZgBLErKbfF5RdrKhzzJ"
                                    "i8i2hnN8r"])
        self.assertTrue("Tool must have a container image to be published."
                        in str(e.exception))

        # Update a descriptor that doesn't have a DOI
        temp_descriptor = tempfile.NamedTemporaryFile(suffix=".json")
        shutil.copyfile(example1_desc, temp_descriptor.name)
        # Make sure that example1.json doesn't have a DOI yet
        with open(temp_descriptor.name, 'r') as fhandle:
            descriptor = json.load(fhandle)
            self.assertIsNone(descriptor.get('doi'))
        # Try to update it
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish",
                  temp_descriptor.name,
                  "--sandbox", "-y", "-v",
                  "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                                    "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r",
                  "--replace"])
        self.assertTrue("To publish an updated version of a previously "
                        "published descriptor, the descriptor must"
                        " contain a DOI"
                        in str(e.exception))

    @mock.patch('requests.get', side_effect=mock_get_publish_bulk())
    @mock.patch('requests.post', side_effect=mock_post_publish_update_only())
    @mock.patch('requests.put', return_value=mock_zenodo_test_api())
    @mock.patch('requests.delete', return_value=mock_zenodo_delete_files())
    def test_publication_replace_no_id(self, mock_get, mock_post, mock_put,
                                       mock_delete):
        self.setup("export")
        example1_desc = self.get_file_path("example1_docker_with_doi.json")
        temp_descriptor = tempfile.NamedTemporaryFile(suffix=".json")
        shutil.copyfile(example1_desc, temp_descriptor.name)

        # Make sure that descriptor has a DOI
        with open(temp_descriptor.name, 'r') as fhandle:
            descriptor = json.load(fhandle)
            self.assertIsNotNone(descriptor.get('doi'))
            old_doi = descriptor['doi']

        # Publish an updated version of an already published descriptor
        doi = bosh(["publish",
                    temp_descriptor.name,
                    "--sandbox", "-y", "-v",
                    "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                                      "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r",
                    "--replace"])
        self.assertTrue(doi)

        # Now descriptor should have a DOI which should be different
        # than the old DOI
        with open(temp_descriptor.name, 'r') as fhandle:
            descriptor = json.load(fhandle)
            self.assertNotEqual(doi, old_doi)
            self.assertEqual(descriptor.get('doi'), doi)

    @mock.patch('requests.get', side_effect=mock_get_publish_bulk())
    @mock.patch('requests.post', return_value=mock_zenodo_no_permission())
    def test_publisher_auth_no_permission(self, mock_get, mock_post):
        # Trying to update a tool published by a different
        # user should inform the user that they do not
        # have permission to publish an update.
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish",
                  self.example1_descriptor,
                  "--sandbox", "--id", "zenodo.12345",
                  "-y", "-v", "--zenodo-token", "12345"])
        self.assertIn("You do not have permission to access this "
                      "resource.", str(e.exception))

    @mock.patch('requests.post', side_effect=mock_post_publish_then_update())
    @mock.patch('requests.put', return_value=mock_zenodo_test_api())
    @mock.patch('requests.delete', return_value=mock_zenodo_delete_files())
    def test_publication_toolname_forwardslash(self,  mock_post,
                                               mock_put, mock_delete):
        test_desc = self.get_file_path("test_forward_slash_toolName.json")
        with open(test_desc, 'r') as fhandle:
            descriptor = json.load(fhandle, object_pairs_hook=OrderedDict)

        # Publish an updated version of an already published descriptor
        doi = bosh(["publish",
                    test_desc,
                    "--sandbox", "-y", "-v",
                    "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                                      "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])

        with open(test_desc, 'w') as fhandle:
            fhandle.write(json.dumps(descriptor, indent=4))

        self.assertEqual('10.5281/zenodo.1234567', doi)
