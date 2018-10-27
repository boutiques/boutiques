from boutiques.bosh import bosh
from unittest import TestCase
import os
import shutil


class TestPull(TestCase):

    def test_pull_by_filename(self):
        # create a temporary directory to download the file
        tmp_dir = "test_pull_example1"
        if not os.path.isdir(tmp_dir):
            os.mkdir(tmp_dir)
        os.chdir(tmp_dir)
        bosh(["pull", "example1_docker.json"])

        assert(os.path.exists("example1_docker.json"))

        os.chdir("..")
        shutil.rmtree(tmp_dir)

    def test_pull_by_id(self):
        # create a temporary directory to download the file
        tmp_dir = "test_pull_example1"
        if not os.path.isdir(tmp_dir):
            os.mkdir(tmp_dir)
        os.chdir(tmp_dir)
        bosh(["pull", "1472823"])

        assert(os.path.exists("example1_docker.json"))

        os.chdir("..")
        shutil.rmtree(tmp_dir)

    def test_pull_not_found(self):
        with self.assertRaises(IOError) as e:
            bosh(["pull", "99999"])
        assert("Descriptor not found" in str(e.exception))
