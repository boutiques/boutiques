from unittest import TestCase
from boutiques.bosh import bosh
from boutiques import __file__ as bfile
import os


class TestPublisher(TestCase):

    def get_boutiques_dir(self):
        return os.path.join(os.path.split(bfile)[0], "..", "..", "..")

    def test_publisher(self):
        self.assertFalse(bosh(["publish", self.get_boutiques_dir(),
                               "test author", "example.com", "--no-github"]))
