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


def mock_mkdir_timeout():
    return OSError("cannot mkdir")


def mock_sleep():
    return None


def mock_clean_up():
    return None


def mock_exists():
    return [False, True]


def mock_sing_pull():
    return ((None, None), 0), None


def mock_os_rename():
    return None


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
        self.assertIn("Local copy", ret.stdout)

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_prepare_sing(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        ret = bosh.execute("prepare",
                           os.path.join(example1_dir,
                                        "example1_sing.json"))
        self.assertIn("Local (boutiques-example1-test.simg)", ret.stdout)

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
        self.assertIn("Local (boutiques-example1-test.simg)", ret.stdout)
        self.assertNotIn("SINGULARITY_PULLFOLDER", os.environ)

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_prepare_sing_specify_imagepath_basename_only(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        ret = bosh.execute("prepare",
                           os.path.join(example1_dir,
                                        "example1_sing.json"),
                           "--imagepath",
                           "boutiques-example1-test.simg")
        self.assertIn("Local (boutiques-example1-test.simg)", ret.stdout)
        self.assertNotIn("SINGULARITY_PULLFOLDER", os.environ)

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
        self.assertIn("Could not pull Singularity image", str(e))

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
        # Specify path for image that does not exist.
        # Mock that another process created the image at that path
        # while this process was waiting.
        ret = bosh.execute("prepare",
                           os.path.join(example1_dir,
                                        "example1_sing.json"),
                           "--imagepath",
                           os.path.join(os.path.expanduser('~'),
                                        "boutiques-example1-test.simg"))
        self.assertIn("Local (boutiques-example1-test.simg)", ret.stdout)

    @mock.patch('os.mkdir', side_effect=mock_mkdir_timeout())
    @mock.patch('time.sleep', side_effect=mock_sleep())
    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_prepare_sing_timeout(self, mock_mkdir, mock_sleep):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        # Specify path for image that does not exist.
        # Mock that another process has the lockdir and this one
        # times out while waiting.
        with pytest.raises(ExecutorError) as e:
            bosh.execute("prepare",
                         os.path.join(example1_dir,
                                      "example1_sing.json"),
                         "--imagepath",
                         os.path.join(os.path.expanduser('~'),
                                      "boutiques-example1-test.simg"))
        self.assertIn("Unable to retrieve Singularity image", str(e))

    @mock.patch('os.mkdir', side_effect=mock_mkdir_timeout())
    @mock.patch('time.sleep', side_effect=mock_sleep())
    @mock.patch('boutiques.localExec.LocalExecutor._singConExists',
                side_effect=mock_exists())
    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_prepare_sing_timeout_success(self, mock_mkdir, mock_sleep,
                                          mock_exists):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        # Specify path for image that does not exist.
        # Mock that another process has the lockdir and this one
        # times out while waiting, but image was created by the
        # other process.
        ret = bosh.execute("prepare",
                           os.path.join(example1_dir,
                                        "example1_sing.json"),
                           "--imagepath",
                           os.path.join(os.path.expanduser('~'),
                                        "boutiques-example1-test.simg"))
        self.assertIn("Local (boutiques-example1-test.simg)", ret.stdout)

    @mock.patch('boutiques.localExec.LocalExecutor._localExecute',
                side_effect=mock_sing_pull())
    @mock.patch('os.rename', side_effect=mock_os_rename())
    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_prepare_sing_pull_success(self, mock_sing_pull, mock_os_rename):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        # Specify path for image that does not exist.
        # Try to pull it and mock that the pull was successful.
        ret = bosh.execute("prepare",
                           os.path.join(example1_dir,
                                        "example1_sing.json"),
                           "--imagepath",
                           os.path.join(os.path.expanduser('~'),
                                        "boutiques-example1-test.simg"))
        self.assertIn("Pulled from docker://boutiques/example1:test",
                      ret.stdout)

    def test_prepare_no_container(self):
        ret = bosh.execute("prepare",
                           os.path.join(self.get_examples_dir(),
                                        "no_container.json"))
        self.assertIn("Descriptor does not specify a container image.",
                      ret.stdout)
