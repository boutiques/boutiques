from boutiques.bosh import bosh
from unittest import TestCase
from boutiques.puller import ZenodoError
import os
import shutil


class TestPull(TestCase):

    def test_pull(self):
        # create a temporary directory to download the file
        tmp_dir = "test_pull_example1"
        if not os.path.isdir(tmp_dir):
            os.mkdir(tmp_dir)
        os.chdir(tmp_dir)
        bosh(["pull", "zenodo.1472823"])

        assert(os.path.exists("example1_docker.json"))

        os.chdir("..")
        shutil.rmtree(tmp_dir)

    def test_pull_missing_prefix(self):
        with self.assertRaises(ZenodoError) as e:
            bosh(["pull", "1472823"])
        assert("Zenodo ID must be prefixed by 'zenodo'" in str(e.exception))

    def test_pull_not_found(self):
        with self.assertRaises(ZenodoError) as e:
            bosh(["pull", "zenodo.99999"])
        assert("Descriptor not found" in str(e.exception))
