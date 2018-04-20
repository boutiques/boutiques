from boutiques import __file__ as bfile
from boutiques.publisher import ZenodoError
from boutiques.bosh import bosh
import json
import subprocess
import shutil
import tempfile
import os.path as op
import sys
if sys.version_info < (2, 7):
    from unittest2 import TestCase
else:
    from unittest import TestCase


class TestPublisher(TestCase):

    def get_examples_dir(self):
        return op.join(op.dirname(bfile),
                       "schema", "examples")

    def test_publication(self):
        example1_dir = op.join(self.get_examples_dir(), "example1")
        example1_desc = op.join(example1_dir, "example1_docker.json")
        temp_descriptor = tempfile.NamedTemporaryFile(suffix=".json")
        shutil.copyfile(example1_desc, temp_descriptor.name)

        # Make sure that example1.json doesn't have a DOI yet
        with open(temp_descriptor.name, 'r') as fhandle:
            descriptor = json.load(fhandle)
            assert(descriptor.get('doi') is None)

        # Test publication of a descriptor that doesn't have a DOI
        doi = bosh(["publish",
                    temp_descriptor.name,
                    "--sandbox", "-y", "-v",
                    "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                    "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        assert(doi)

        # Now descriptor should have a DOI
        with open(temp_descriptor.name, 'r') as fhandle:
            descriptor = json.load(fhandle)
            assert(descriptor.get('doi') == doi)

        # Test publication of a descriptor that already has a DOI
        with self.assertRaises(ZenodoError) as e:
          bosh(["publish",
                temp_descriptor.name,
                "--sandbox", "-y", "-v",
                "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"])
        self.assertTrue("Desriptor already has a DOI" in str(e.exception))

    def test_publisher_auth(self):
        example1_dir = op.join(self.get_examples_dir(), "example1")

        # Bad token should fail
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish",
                  op.join(example1_dir, "example1_docker.json"),
                  "--sandbox",
                  "-y", "-v", "--zenodo-token", "12345"])
        self.assertTrue("Cannot authenticate to Zenodo" in str(e.exception))

        # No token should fail
        with self.assertRaises(ZenodoError) as e:
          bosh(["publish",
                 op.join(example1_dir,
                         "example1_docker.json"),
                 "--sandbox", "-y", "-v"])
        self.assertTrue("Cannot authenticate to Zenodo" in str(e.exception))

        # Right token should work
        self.assertTrue(bosh, ["publish",
                               op.join(example1_dir,
                                       "example1_docker.json"),
                               "--sandbox", "-y", "-v",
                               "--zenodo-token",
                               "hAaW2wSBZMskxpfigTYHcuDrC"
                               "PWr2VeQZgBLErKbfF5RdrKhzzJ"
                               "i8i2hnN8r"])

        # Now no token should work (config file must have been updated)
        self.assertTrue(bosh, ["publish",
                               op.join(example1_dir,
                                       "example1_docker.json"),
                               "--sandbox", "-y", "-v"])

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
