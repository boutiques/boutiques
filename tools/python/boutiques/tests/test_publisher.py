from boutiques import __file__ as bfile
from boutiques.publisher import ZenodoError
from boutiques.bosh import bosh
import simplejson as json
import subprocess
import shutil
import tempfile
import os
import os.path as op
import sys
import mock
from boutiques_mocks import *
if sys.version_info < (2, 7):
    from unittest2 import TestCase
else:
    from unittest import TestCase


def mock_get_publish_then_update():
    mock_record = MockZenodoRecord(1234567, "Example Boutiques Tool")
    return ([mock_zenodo_test_api_fail(),
            mock_zenodo_test_api(),
            mock_zenodo_search([]),
            mock_zenodo_test_api_fail(),
            mock_zenodo_test_api(),
            mock_zenodo_search([mock_record])])


# for publishing updates with --replace option
def mock_get_no_search():
    return ([mock_zenodo_test_api_fail(),
            mock_zenodo_test_api()])


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


def mock_put():
    return mock_zenodo_update_metadata()


def mock_delete():
    return mock_zenodo_delete_files()


def mock_get_auth_fail():
    return mock_zenodo_test_api_fail()


def mock_post_no_permission():
    return mock_zenodo_no_permission()


class TestPublisher(TestCase):

    def get_examples_dir(self):
        return op.join(op.dirname(bfile),
                       "schema", "examples")

    @mock.patch('requests.get', side_effect=mock_get_publish_then_update())
    @mock.patch('requests.post', side_effect=mock_post_publish_then_update())
    @mock.patch('requests.put', return_value=mock_put())
    @mock.patch('requests.delete', return_value=mock_delete())
    def test_publication(self, mock_get, mock_post, mock_put, mock_delete):
        example1_dir = op.join(self.get_examples_dir(), "example1")
        example1_desc = op.join(example1_dir, "example1_docker.json")
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
        example1_desc_updated = op.join(example1_dir,
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

    @mock.patch('requests.get', return_value=mock_get_auth_fail())
    def test_publisher_auth(self, mock_get):
        example1_dir = op.join(self.get_examples_dir(), "example1")

        # Bad token should fail
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish",
                  op.join(example1_dir, "example1_docker.json"),
                  "--sandbox",
                  "-y", "-v", "--zenodo-token", "12345"])
        self.assertIn("Cannot authenticate to Zenodo", str(e.exception))

        # No token should fail
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish",
                 op.join(example1_dir,
                         "example1_docker.json"),
                 "--sandbox", "-y", "-v"])
        self.assertIn("Cannot authenticate to Zenodo", str(e.exception))

    # Note that this test does not use mocks as the mocks don't seem
    # to work with subprocess.Popen.
    def test_publisher_auth_fail_cli(self):
        example1_dir = op.join(self.get_examples_dir(), "example1")
        command = ("bosh publish " + op.join(example1_dir,
                                             "example1_docker.json") +
                   " --sandbox -y -v "
                   "--zenodo-token 12345")
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate()
        self.assertTrue(process.returncode)

    @mock.patch('requests.get', side_effect=mock_get_no_search())
    @mock.patch('requests.post', side_effect=mock_post_publish_update_only())
    @mock.patch('requests.put', return_value=mock_put())
    @mock.patch('requests.delete', return_value=mock_delete())
    def test_publication_replace_with_id(self, mock_get, mock_post, mock_put,
                                         mock_delete):
        example1_dir = op.join(self.get_examples_dir(), "example1")
        example1_desc = op.join(example1_dir, "example1_docker.json")
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
        with self.assertRaises(ZenodoError) as e:
            wrong_id = bosh(["publish",
                             "whatever.json",
                             "--sandbox", "-y", "-v",
                             "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                                               "PWr2VeQZgBLErKbfF5RdrKhzzJ"
                                               "i8i2hnN8r",
                             "--id", "this_is_a_wrong_id"])
        self.assertTrue("Zenodo ID must be prefixed by 'zenodo'"
                        in str(e.exception))

        # Publish a descriptor that doesn't have an author
        good_desc = op.join(self.get_examples_dir(), "good.json")
        temp_descriptor = tempfile.NamedTemporaryFile(suffix=".json")
        shutil.copyfile(good_desc, temp_descriptor.name)
        with self.assertRaises(ZenodoError) as e:
            no_author = bosh(["publish",
                              temp_descriptor.name,
                              "--sandbox", "-y", "-v",
                              "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                                                "PWr2VeQZgBLErKbfF5RdrKhzzJ"
                                                "i8i2hnN8r"])
        self.assertTrue("Tool must have an author to be published."
                        in str(e.exception))

        # Publish a descriptor that doesn't have a container image
        good_desc = op.join(self.get_examples_dir(), "no_container.json")
        temp_descriptor = tempfile.NamedTemporaryFile(suffix=".json")
        shutil.copyfile(good_desc, temp_descriptor.name)
        with self.assertRaises(ZenodoError) as e:
            no_container = bosh(["publish",
                                 temp_descriptor.name,
                                 "--sandbox", "-y", "-v",
                                 "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                                                   "PWr2VeQZgBLErKbfF5RdrKhzzJ"
                                                   "i8i2hnN8r"])
        self.assertTrue("Tool must have a container image to be published."
                        in str(e.exception))

        # Update a descriptor that doesn't have a DOI
        example1_dir = op.join(self.get_examples_dir(), "example1")
        example1_desc = op.join(example1_dir, "example1_docker.json")
        temp_descriptor = tempfile.NamedTemporaryFile(suffix=".json")
        shutil.copyfile(example1_desc, temp_descriptor.name)
        # Make sure that example1.json doesn't have a DOI yet
        with open(temp_descriptor.name, 'r') as fhandle:
            descriptor = json.load(fhandle)
            self.assertIsNone(descriptor.get('doi'))
        # Try to update it
        with self.assertRaises(ZenodoError) as e:
            doi = bosh(["publish",
                        temp_descriptor.name,
                        "--sandbox", "-y", "-v",
                        "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                                          "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r",
                        "--replace"])
        self.assertTrue("To publish an updated version of a previously "
                        "published descriptor, the descriptor must"
                        " contain a DOI"
                        in str(e.exception))

    @mock.patch('requests.get', side_effect=mock_get_no_search())
    @mock.patch('requests.post', side_effect=mock_post_publish_update_only())
    @mock.patch('requests.put', return_value=mock_put())
    @mock.patch('requests.delete', return_value=mock_delete())
    def test_publication_replace_no_id(self, mock_get, mock_post, mock_put,
                                       mock_delete):
        example1_dir = op.join(self.get_examples_dir(), "example1")
        example1_desc = op.join(example1_dir, "example1_docker_with_doi.json")
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

    @mock.patch('requests.get', side_effect=mock_get_no_search())
    @mock.patch('requests.post', return_value=mock_post_no_permission())
    def test_publisher_auth_no_permission(self, mock_get, mock_post):
        example1_dir = op.join(self.get_examples_dir(), "example1")

        # Trying to update a tool published by a different
        # user should inform the user that they do not
        # have permission to publish an update.
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish",
                  op.join(example1_dir, "example1_docker.json"),
                  "--sandbox", "--id", "zenodo.12345",
                  "-y", "-v", "--zenodo-token", "12345"])
        self.assertIn("You do not have permission to access this "
                      "resource.", str(e.exception))
