from unittest import TestCase
from boutiques.bosh import bosh
from boutiques import __file__ as bfile
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
