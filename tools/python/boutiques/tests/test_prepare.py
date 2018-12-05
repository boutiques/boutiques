#!/usr/bin/env python

import os
import subprocess
import pytest
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh
from boutiques.localExec import ExecutorError


class TestPrepare(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_prepare_docker(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        ret = bosh.execute("prepare",
                           os.path.join(example1_dir,
                                        "example1_docker.json"))
        assert("Local copy" in ret.stdout)

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_prepare_sing(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        ret = bosh.execute("prepare",
                           os.path.join(example1_dir,
                                        "example1_sing.json"))
        assert("Local (boutiques-example1-test.simg)" in ret.stdout)

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_prepare_sing_specify_imagepath(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        with pytest.raises(ExecutorError) as e:
            ret = bosh.execute("prepare",
                               os.path.join(example1_dir,
                                            "example1_sing.json"),
                               "--imagepath", os.path.expanduser('~'))
        assert("Could not pull Singularity image" in str(e))
        assert("SINGULARITY_PULLFOLDER" not in os.environ)

    def test_prepare_no_container(self):
        ret = bosh.execute("prepare",
                           os.path.join(self.get_examples_dir(),
                                        "no_container.json"))
        assert("Descriptor does not specify a container image." in ret.stdout)
