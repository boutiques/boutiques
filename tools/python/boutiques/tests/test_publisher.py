from unittest import TestCase
from boutiques import __file__ as bfile
from boutiques.publisher import ZenodoError
from boutiques.bosh import bosh
import subprocess
import os


class TestPublisher(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def test_publisher(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        print(os.path.join(example1_dir, "example1.json"))
        self.assertFalse(bosh(["publish",
                               os.path.join(example1_dir, "example1.json"),
                               "Test author", "Test affiliation",
                               "--sandbox", "-y", "-v",
                               "--zenodo-token", "hAaW2wSBZMskxpfigTYHcuDrC"
                               "PWr2VeQZgBLErKbfF5RdrKhzzJi8i2hnN8r"]))

        self.assertFalse(bosh(["publish",
                               os.path.join(example1_dir, "example1.json"),
                               "Test author", "Test affiliation",
                               "--sandbox", "-y", "-v"]))

    def test_publisher_auth_fail(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        with self.assertRaises(ZenodoError) as e:
            bosh(["publish", os.path.join(example1_dir, "example1.json"),
                  "Test author", "Test affiliation", "--sandbox",
                  "-y", "-v", "--zenodo-token", "12345"])
        print(e.exception)
        self.assertTrue("Cannot authenticate to Zenodo" in e.exception.message)

    def test_publisher_auth_fail_cli(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        command = ("bosh publish " + os.path.join(example1_dir,
                                                  "example1.json") +
                   "'Test author' 'Test affiliation' --sandbox -y -v "
                   "--zenodo-token 12345")
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate()
        self.assertTrue(process.returncode)
