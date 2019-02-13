#!/usr/bin/env python

import os
import subprocess
import pytest
from boutiques import __file__ as bfile
import boutiques as bosh
from boutiques.localExec import ExecutorError
import mock
import sys
from boutiques_mocks import *
if sys.version_info < (2, 7):
    from unittest2 import TestCase
else:
    from unittest import TestCase


def mock_mkdir():
    return [OSError("cannot mkdir"), None]


def mock_clean_up():
    return None


def mock_exists():
    return [False, True]


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
        ret = bosh.execute("prepare",
                           os.path.join(example1_dir,
                                        "example1_sing.json"),
                           "--imagepath",
                           os.path.join(os.getcwd(),
                                        "boutiques-example1-test.simg"))
        assert("Local (boutiques-example1-test.simg)" in ret.stdout)
        assert("SINGULARITY_PULLFOLDER" not in os.environ)

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_prepare_sing_image_does_not_exist(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        # Specify the wrong path for the image
        # Will try to pull it and pull will fail
        with pytest.raises(ExecutorError) as e:
            bosh.execute("prepare",
                         os.path.join(example1_dir,
                                      "example1_sing.json"),
                         "--imagepath",
                         os.path.join(os.path.expanduser('~'),
                                      "boutiques-example1-test.simg"))
        assert("Could not pull Singularity image" in str(e))

    @mock.patch('os.mkdir', side_effect=mock_mkdir())
    @mock.patch('boutiques.localExec.LocalExecutor._singConExists',
                side_effect=mock_exists())
    @mock.patch('boutiques.localExec.LocalExecutor._cleanUpAfterSingPull',
                side_effect=mock_clean_up())
    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_prepare_sing_multiple_processes(self, mock_mkdir, mock_exists,
                                             mock_clean_up):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        # Specify the wrong path for the image, but mock that another process
        # created the image at that path while this process was waiting
        ret = bosh.execute("prepare",
                           os.path.join(example1_dir,
                                        "example1_sing.json"),
                           "--imagepath",
                           os.path.join(os.path.expanduser('~'),
                                        "boutiques-example1-test.simg"))
        assert ("Local (boutiques-example1-test.simg)" in ret.stdout)

    def test_prepare_no_container(self):
        ret = bosh.execute("prepare",
                           os.path.join(self.get_examples_dir(),
                                        "no_container.json"))
        assert("Descriptor does not specify a container image." in ret.stdout)
