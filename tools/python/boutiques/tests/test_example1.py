#!/usr/bin/env python

import os
import subprocess
import pytest
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh


class TestExample1(TestCase):

    def get_examples_dir(self):
        return os.path.join(os.path.dirname(bfile),
                            "schema", "examples")

    def clean_up(self):
        fls = os.listdir('./')
        for fl in fls:
            if (fl.startswith('log') or fl.startswith('config')) and \
               fl.endswith('.txt'):
                os.remove(fl)

    def test_example1_no_exec(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.assertFalse(bosh.execute("simulate",
                                      os.path.join(example1_dir,
                                                   "example1_docker.json"),
                                      "-i",
                                      os.path.join(example1_dir,
                                                   "invocation.json"))[2])

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        self.assertFalse(bosh.execute("launch",
                                      os.path.join(example1_dir,
                                                   "example1_docker.json"),
                                      os.path.join(example1_dir,
                                                   "invocation.json"))[2])
        self.clean_up()
        self.assertFalse(bosh.execute("launch",
                                      os.path.join(example1_dir,
                                                   "example1_docker.json"),
                                      "-x",
                                      os.path.join(example1_dir,
                                                   "invocation.json"))[2])

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_example1_exec_singularity(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        self.assertFalse(bosh.execute("launch",
                                      os.path.join(example1_dir,
                                                   "example1_sing.json"),
                                      os.path.join(example1_dir,
                                                   "invocation.json"))[2])
        self.clean_up()
        self.assertFalse(bosh.execute("launch",
                                      os.path.join(example1_dir,
                                                   "example1_sing.json"),
                                      "-x",
                                      os.path.join(example1_dir,
                                                   "invocation.json"))[2])

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_missing_script(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        sout, serr, ecode, emsg = bosh.execute(
                                   "launch",
                                   os.path.join(example1_dir,
                                                "example1_docker.json"),
                                   os.path.join(example1_dir,
                                                "invocation_missing_script.json"
                                                ))
        self.assertTrue('Example Boutiques Tool ERR (2):'
                        ' File does not exist!' in emsg)

    def test_example1_no_exec_random(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.assertFalse(bosh.execute("simulate",
                                      os.path.join(example1_dir,
                                                   "example1_docker.json"),
                                      "-r", "3")[2])
