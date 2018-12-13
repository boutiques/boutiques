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
        assert(ret.stdout != "" and ret.stderr == "" and ret.exit_code == 0
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

        # Make sure stdout and stderr are not printed on the fly
        # for non-streaming mode
        out, err = self.capfd.readouterr()
        assert("This is stdout" not in out)
        assert("This is stderr" not in out)

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

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_stream_output(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        ret = bosh.execute("launch",
                           os.path.join(example1_dir,
                                        "example1_docker.json"),
                           "-s",
                           os.path.join(example1_dir,
                                        "invocation.json"))

        # Make sure stdout and stderr are printed on the fly for
        # streaming mode
        out, err = self.capfd.readouterr()
        assert("This is stdout" in out)
        assert("This is stderr" in out)

        print(ret)
        assert(ret.stdout is None)
        assert(ret.stderr is None)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_inv_as_json_obj(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        invocationStr = open(os.path.join(example1_dir,
                                          "invocation.json")).read()
        ret = bosh.execute("launch",
                           os.path.join(example1_dir,
                                        "example1_docker.json"),
                           invocationStr)

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

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_desc_as_json_obj(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        descStr = open(os.path.join(example1_dir,
                                    "example1_docker.json")).read()
        ret = bosh.execute("launch",
                           descStr,
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

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_json_string_invalid(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        invocationStr = open(os.path.join(example1_dir,
                                          "invocation_invalid.json")).read()
        with pytest.raises(ExecutorError) as e:
                bosh.execute("launch",
                             os.path.join(example1_dir,
                                          "example1_docker.json"),
                             invocationStr)
        assert("Cannot parse input" in str(e))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_from_zenodo(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        ret = bosh.execute("launch", "zenodo.1472823",
                           os.path.join(example1_dir,
                                        "invocation.json"))

        # Make sure stdout and stderr are not printed on the fly
        # for non-streaming mode
        out, err = self.capfd.readouterr()
        assert("This is stdout" not in out)
        assert("This is stderr" not in out)

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
        ret = bosh.execute("launch", "zenodo.1472823",
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
        with pytest.raises(ExecutorError) as e:
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

    def test_example1_exec_fail_cli(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        self.clean_up()
        command = ("bosh exec launch " +
                   os.path.join(example1_dir,
                                "example1_docker.json") + " " +
                   os.path.join(example1_dir,
                                "invocation_missing_script.json"))
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate()
        assert(process.returncode == 2), command

    def test_example1_no_exec_random(self):
        example1_dir = os.path.join(self.get_examples_dir(), "example1")
        ret = bosh.execute("simulate",
                           os.path.join(example1_dir,
                                        "example1_docker.json"))
        print(ret)
        assert(ret.stdout != ""
               and ret.stderr == ""
               and ret.exit_code == 0
               and ret.error_message == "")

    # Captures the stdout and stderr during test execution
    # and returns them as a tuple in readouterr()
    @pytest.fixture(autouse=True)
    def capfd(self, capfd):
        self.capfd = capfd
