from boutiques import __file__ as bfile
from boutiques.publisher import ZenodoError
from boutiques.bosh import bosh
import subprocess
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

    def test_publisher(self):
        example1_dir = op.join(self.get_examples_dir(), "example1")
        print(op.join(example1_dir, "example1_docker.json"))
        self.assertRaises(ZenodoError, bosh, ["publish",
                                              op.join(example1_dir,
                                                      "example1_docker.json"),
                                              "Test author",
                                              "Test affiliation",
                                              "--sandbox", "-y", "-v"])

        self.assertRaises(ZenodoError, bosh, ["publish",
                                              op.join(example1_dir,
                                                      "example1_docker.json"),
                                              "Test author",
                                              "Test affiliation",
                                              "--sandbox", "-y", "-v",
                                              "--zenodo-token", "badtoken"])

        self.assertFalse(bosh(["publish",
                               op.join(example1_dir, "example1_docker.json"),
                               "Test author", "Test affiliation",
                               "--sandbox", "-y", "-v",
                               "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                               "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"]))

        self.assertFalse(bosh(["publish",
                               op.join(example1_dir, "example1_docker.json"),
                               "Test author", "Test affiliation",
                               "--sandbox", "-y", "-v"]))

    def test_publisher_auth_fail(self):
        example1_dir = op.join(self.get_examples_dir(), "example1")
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish", op.join(example1_dir, "example1_docker.json"),
                  "Test author", "Test affiliation", "--sandbox",
                  "-y", "-v", "--zenodo-token", "12345"])
        print(e.exception)
        self.assertTrue("Cannot authenticate to Zenodo" in str(e.exception))

    def test_publisher_auth_fail_cli(self):
        example1_dir = op.join(self.get_examples_dir(), "example1")
        command = ("bosh publish " + op.join(example1_dir,
                                             "example1_docker.json") +
                   "'Test author' 'Test affiliation' --sandbox -y -v "
                   "--zenodo-token 12345")
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate()
        self.assertTrue(process.returncode)
