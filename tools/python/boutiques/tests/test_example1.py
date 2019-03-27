#!/usr/bin/env python

import os
import subprocess
import pytest
from boutiques.util.BaseTest import BaseTest
import boutiques as bosh
from boutiques.localExec import ExecutorError
import mock
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord


def mock_get():
    mock_record = MockZenodoRecord(1472823, "Example Boutiques Tool", "",
                                   "https://zenodo.org/api/files/"
                                   "e5628764-fc57-462e-9982-65f8d6fdb487/"
                                   "example1_docker.json")
    return mock_zenodo_search([mock_record])


class TestExample1(BaseTest):

    def setUp(self):
        self.setup("example1")

    def clean_up(self):
        fls = os.listdir('./')
        for fl in fls:
            if (fl.startswith('log') or fl.startswith('config')) and \
               fl.endswith('.txt'):
                os.remove(fl)

    def test_example1_no_exec(self):
        self.assert_successful_return(
            bosh.execute("simulate",
                         self.get_file_path("example1_docker.json"),
                         "-i",
                         self.get_file_path("invocation.json")),
            aditional_assertions=self.assert_only_stdout)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker(self):
        self.clean_up()
        ret = bosh.execute("launch",
                           self.get_file_path("example1_docker.json"),
                           self.get_file_path("invocation.json"),
                           "--skip-data-collection")

        # Make sure stdout and stderr are not printed on the fly
        # for non-streaming mode
        out, err = self.capfd.readouterr()
        self.assertNotIn("This is stdout", out)
        self.assertNotIn("This is stderr", out)

        self.assert_successful_return(
            ret, ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

        self.clean_up()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_docker.json"),
                         "-x",
                         self.get_file_path("invocation.json"),
                         "--skip-data-collection"),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_stream_output(self):
        self.clean_up()
        ret = bosh.execute("launch",
                           self.get_file_path("example1_docker.json"),
                           "-s",
                           self.get_file_path("invocation.json"),
                           "--skip-data-collection")

        # Make sure stdout and stderr are printed on the fly for
        # streaming mode
        out, err = self.capfd.readouterr()
        self.assertIn("This is stdout", out)
        self.assertIn("This is stderr", out)

        self.assertIsNone(ret.stdout)
        self.assertIsNone(ret.stderr)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_inv_as_json_obj(self):
        self.clean_up()
        invocationStr = open(self.get_file_path("invocation.json")).read()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_docker.json"),
                         invocationStr,
                         "--skip-data-collection"),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

        self.clean_up()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_docker.json"),
                         "-x",
                         self.get_file_path("invocation.json"),
                         "--skip-data-collection"),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_desc_as_json_obj(self):
        self.clean_up()
        descStr = open(self.get_file_path("example1_docker.json")).read()
        self.assert_successful_return(
            bosh.execute("launch",
                         descStr,
                         self.get_file_path("invocation.json"),
                         "--skip-data-collection"),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

        self.clean_up()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_docker.json"),
                         "-x",
                         self.get_file_path("invocation.json"),
                         "--skip-data-collection"),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_json_string_invalid(self):
        self.clean_up()
        invocationStr = open(
            self.get_file_path("invocation_invalid.json")).read()
        with pytest.raises(ExecutorError) as e:
            bosh.execute("launch",
                         self.get_file_path("example1_docker.json"),
                         invocationStr,
                         "--skip-data-collection")
        self.assertIn("Cannot parse input", str(e))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    @mock.patch('requests.get', return_value=mock_get())
    def test_example1_exec_docker_from_zenodo(self, mock_get):
        self.clean_up()
        ret = bosh.execute("launch", "zenodo.1472823",
                           self.get_file_path("invocation.json"),
                           "--skip-data-collection")

        # Make sure stdout and stderr are not printed on the fly
        # for non-streaming mode
        out, err = self.capfd.readouterr()
        self.assertNotIn("This is stdout", out)
        self.assertNotIn("This is stderr", out)
        self.assert_successful_return(ret,
                                      ["log-4-coin;plop.txt"], 2,
                                      self.assert_reflected_output)

        self.clean_up()
        self.assert_successful_return(
            bosh.execute("launch", "zenodo.1472823",
                         "-x",
                         self.get_file_path("invocation.json"),
                         "--skip-data-collection"),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

    @pytest.mark.skipif(
        subprocess.Popen("type singularity", shell=True).wait(),
        reason="Singularity not installed")
    def test_example1_exec_singularity(self):
        self.clean_up()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_sing.json"),
                         self.get_file_path("invocation_sing.json"),
                         "--skip-data-collection"),
            ["log-4.txt"], 2,
            self.assert_reflected_output)

        self.clean_up()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_sing.json"),
                         "-x",
                         self.get_file_path("invocation_sing.json")),
            ["log-4.txt"], 2,
            self.assert_reflected_output)

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_example1_crash_pull_singularity(self):
        self.clean_up()
        with pytest.raises(ExecutorError) as e:
            bosh.execute("launch",
                         self.get_file_path(
                             "example1_sing_crash_pull.json"),
                         self.get_file_path(
                             "invocation_sing.json"),
                         "--skip-data-collection")
        self.assertIn("Could not pull Singularity image", str(e))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_missing_script(self):
        self.clean_up()
        self.assert_failed_return(
            bosh.execute("launch",
                         self.get_file_path("example1_docker.json"),
                         self.get_file_path(
                             "invocation_missing_script.json"),
                         "--skip-data-collection"),
            2, "File does not exist!", ["log-4-pwet.txt"], 1)

    def test_example1_exec_fail_cli(self):
        self.clean_up()
        command = ("bosh exec launch " +
                   self.get_file_path("example1_docker.json") + " " +
                   self.get_file_path("invocation_missing_script.json") +
                   " --skip-data-collection")
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate()
        assert(process.returncode == 2), command

    def test_example1_no_exec_random(self):
        self.assert_successful_return(
            bosh.execute("simulate",
                         self.get_file_path("example1_docker.json")),
            aditional_assertions=self.assert_only_stdout)

    # Captures the stdout and stderr during test execution
    # and returns them as a tuple in readouterr()
    @pytest.fixture(autouse=True)
    def capfd(self, capfd):
        self.capfd = capfd
