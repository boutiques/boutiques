#!/usr/bin/env python

import os
import subprocess
import pytest
from unittest import TestCase
from boutiques import __file__ as bfile
import boutiques as bosh
from boutiques.localExec import ExecutorError


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
        ret = bosh.execute("simulate",
                           os.path.join(example1_dir,
                                        "example1_docker.json"),
                           "-i",
                           os.path.join(example1_dir,
                                        "invocation.json"))
        assert(ret.stdout == "" and ret.stderr == "" and ret.exit_code == 0
               and ret.error_message == "" and ret.missing_files == [])

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        ret = bosh.execute("launch",
                           os.path.join(example1_dir,
                                        "example1_docker.json"),
                           os.path.join(example1_dir,
                                        "invocation.json"))

        print(ret)
        assert("This is stdout" in ret.stdout)
        assert("This is stderr" in ret.stderr)
        assert(ret.exit_code == 0)
        assert(ret.error_message == "")
        assert(ret.missing_files == [])
        assert(len(ret.output_files) == 2)
        assert(ret.output_files[0].file_name == "log-4-coin;plop.txt" or
               ret.output_files[1].file_name == "log-4-coin;plop.txt")

        self.clean_up()
        ret = bosh.execute("launch",
                           os.path.join(example1_dir,
                                        "example1_docker.json"),
                           "-x",
                           os.path.join(example1_dir,
                                        "invocation.json"))
        print(ret)
        assert("This is stdout" in ret.stdout)
        assert("This is stderr" in ret.stderr)
        assert(ret.exit_code == 0)
        assert(ret.error_message == "")
        assert(ret.missing_files == [])
        assert(len(ret.output_files) == 2)
        assert(ret.output_files[0].file_name == "log-4-coin;plop.txt" or
               ret.output_files[1].file_name == "log-4-coin;plop.txt")

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_example1_exec_singularity(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        ret = bosh.execute("launch",
                           os.path.join(example1_dir,
                                        "example1_sing.json"),
                           os.path.join(example1_dir,
                                        "invocation_sing.json"))
        print(ret)
        assert("This is stdout" in ret.stdout)
        assert("This is stderr" in ret.stderr)
        assert(ret.exit_code == 0)
        assert(ret.error_message == "")
        assert(ret.missing_files == [])
        assert(len(ret.output_files) == 2)
        assert(ret.output_files[0].file_name == "log-4.txt" or
               ret.output_files[1].file_name == "log-4.txt")

        self.clean_up()
        ret = bosh.execute("launch",
                           os.path.join(example1_dir,
                                        "example1_sing.json"),
                           "-x",
                           os.path.join(example1_dir,
                                        "invocation_sing.json"))
        print(ret)
        assert("This is stdout" in ret.stdout)
        assert("This is stderr" in ret.stderr)
        assert(ret.exit_code == 0)
        assert(ret.error_message == "")
        assert(ret.missing_files == [])
        assert(len(ret.output_files) == 2)
        assert(ret.output_files[0].file_name == "log-4.txt" or
               ret.output_files[1].file_name == "log-4.txt")

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_example1_crash_pull_singularity(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        with pytest.raises(ExecutionError) as e:
                bosh.execute("launch",
                             os.path.join(example1_dir,
                                          "example1_sing_crash_pull.json"),
                             os.path.join(example1_dir,
                                          "invocation_sing.json"))
        assert("Could not pull Singularity image" in str(e))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_missing_script(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        ret = bosh.execute("launch",
                           os.path.join(example1_dir,
                                        "example1_docker.json"),
                           os.path.join(example1_dir,
                                        "invocation_missing_script.json"))
        print(ret)
        assert(ret.exit_code == 2)
        assert(ret.error_message == "File does not exist!")
        assert(len(ret.missing_files) == 1)
        assert(ret.missing_files[0].file_name == "log-4-pwet.txt")

    def test_example1_no_exec_random(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        ret = bosh.execute("simulate",
                           os.path.join(example1_dir,
                                        "example1_docker.json"),
                           "-r", "3")
        print(ret)
        assert(ret.stdout == ""
               and ret.stderr == ""
               and ret.exit_code == 0
               and ret.error_message == "")
