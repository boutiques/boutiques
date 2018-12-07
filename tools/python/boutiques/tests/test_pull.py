from boutiques.bosh import bosh
from unittest import TestCase
from boutiques.puller import ZenodoError
import os


class TestPull(TestCase):

    def test_pull(self):
        bosh(["pull", "zenodo.1472823", "-y"])
        cache_dir = os.path.join(os.path.expanduser('~'), ".cache", "boutiques")
        assert(os.path.exists(os.path.join(cache_dir, "example1_docker.json")))

    def test_pull_missing_prefix(self):
        with self.assertRaises(ZenodoError) as e:
            bosh(["pull", "1472823", "-y"])
        assert("Zenodo ID must be prefixed by 'zenodo'" in str(e.exception))

    def test_pull_not_found(self):
        with self.assertRaises(ZenodoError) as e:
            bosh(["pull", "zenodo.99999", "-y"])
        assert("Descriptor not found" in str(e.exception))
