#!/usr/bin/env python

import os
import subprocess
import pytest
from boutiques.util.BaseTest import BaseTest
import boutiques as bosh
from boutiques.localExec import ExecutorError
from boutiques.util.utils import LoadError
import mock
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord,\
    example_boutiques_tool
from boutiques import __file__ as bfile
from shutil import copy2, rmtree
import simplejson as json


def clean_up():
    fls = os.listdir('./')
    for fl in fls:
        if (fl.startswith('log') or fl.startswith('config')) and \
           fl.endswith('.txt'):
            os.remove(fl)


class TestExample1(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("example1")

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
        clean_up()
        ret = bosh.execute("launch",
                           self.get_file_path("example1_docker.json"),
                           self.get_file_path("invocation.json"),
                           "--skip-data-collection",
                           "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                           "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2")))

        # Make sure stdout and stderr are not printed on the fly
        # for non-streaming mode
        out, err = self.capfd.readouterr()
        self.assertNotIn("This is stdout", out)
        self.assertNotIn("This is stderr", out)

        self.assert_successful_return(
            ret, ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

        clean_up()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_docker.json"),
                         "-x",
                         self.get_file_path("invocation.json"),
                         "--skip-data-collection",
                         "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                         "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2"))),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_stream_output(self):
        clean_up()
        ret = bosh.execute("launch",
                           self.get_file_path("example1_docker.json"),
                           "-s",
                           self.get_file_path("invocation.json"),
                           "--skip-data-collection",
                           "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                           "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2")))

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
        clean_up()
        invocationStr = open(self.get_file_path("invocation.json")).read()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_docker.json"),
                         invocationStr,
                         "--skip-data-collection",
                         "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                         "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2"))),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

        clean_up()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_docker.json"),
                         "-x",
                         self.get_file_path("invocation.json"),
                         "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                         "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2")),
                         "--skip-data-collection"),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_desc_as_json_obj(self):
        clean_up()
        descStr = open(self.get_file_path("example1_docker.json")).read()
        self.assert_successful_return(
            bosh.execute("launch",
                         descStr,
                         self.get_file_path("invocation.json"),
                         "--skip-data-collection",
                         "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                         "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2"))),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

        clean_up()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_docker.json"),
                         "-x",
                         self.get_file_path("invocation.json"),
                         "--skip-data-collection",
                         "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                         "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2"))),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_json_string_invalid(self):
        clean_up()
        invocationStr = open(
            self.get_file_path("invocation_invalid.json")).read()
        with pytest.raises(LoadError) as e:
            bosh.execute("launch",
                         self.get_file_path("example1_docker.json"),
                         "-u",
                         invocationStr,
                         "--skip-data-collection")
        self.assertIn("Cannot parse input", str(e.getrepr(style='long')))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    @mock.patch('requests.get', return_value=mock_zenodo_search([example_boutiques_tool]))
    def test_example1_exec_docker_from_zenodo(self, _):
        clean_up()
        ret = bosh.execute("launch",
                           "zenodo." + str(example_boutiques_tool.id),
                           self.get_file_path("invocation.json"),
                           "--skip-data-collection",
                           "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                           "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2")))

        # Make sure stdout and stderr are not printed on the fly
        # for non-streaming mode
        out, err = self.capfd.readouterr()
        self.assertNotIn("This is stdout", out)
        self.assertNotIn("This is stderr", out)
        self.assert_successful_return(ret,
                                      ["log-4-coin;plop.txt"], 2,
                                      self.assert_reflected_output)

        clean_up()
        self.assert_successful_return(
            bosh.execute("launch", "zenodo." + str(example_boutiques_tool.id),
                         "-x",
                         self.get_file_path("invocation.json"),
                         "--skip-data-collection",
                         "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                         "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2"))),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    @mock.patch('requests.get', return_value=mock_zenodo_search([example_boutiques_tool]))
    def test_example1_exec_docker_from_zenodo_desc2func(self, _):
        # No mode provided, defaults to 'launch'
        clean_up()
        from boutiques.descriptor2func import function
        example_tool = function("zenodo." + str(example_boutiques_tool.id))
        ret = example_tool(str_input_list=['a', 'b', 'c'],
                           str_input="coin;plop",
                           file_input='./setup.py',
                           file_list_input=['./setup.py', 'requirements.txt'],
                           list_int_input=[1, 2, 3],
                           config_num=4,
                           enum_input='val1')
        print(ret)
        self.assert_successful_return(ret,
                                      ["log-4-coin;plop.txt"], 2,
                                      self.assert_reflected_output)

        # Launch mode
        clean_up()
        ret = example_tool('launch',
                           str_input_list=['a', 'b', 'c'],
                           str_input="coin;plop",
                           file_input='./setup.py',
                           file_list_input=['./setup.py', 'requirements.txt'],
                           list_int_input=[1, 2, 3],
                           config_num=4,
                           enum_input='val1')
        self.assert_successful_return(ret,
                                      ["log-4-coin;plop.txt"], 2,
                                      self.assert_reflected_output)

        # Simulate with invocation
        clean_up()
        ret = example_tool('simulate',
                           str_input_list=['a', 'b', 'c'],
                           str_input="coin;plop",
                           file_input='./setup.py',
                           file_list_input=['./setup.py', 'requirements.txt'],
                           list_int_input=[1, 2, 3],
                           config_num=4,
                           enum_input='val1')
        self.assert_successful_return(
                            ret,
                            aditional_assertions=self.assert_only_stdout)

        # Simulate without invocation
        clean_up()
        ret = example_tool('simulate')
        self.assertIn('exampleTool1.py -c', ret.stdout)

    @pytest.mark.skipif(
        subprocess.Popen("type singularity", shell=True).wait(),
        reason="Singularity not installed")
    def test_example1_exec_singularity(self):
        clean_up()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_sing.json"),
                         self.get_file_path("invocation_sing.json"),
                         "--skip-data-collection",
                         "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                         "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2"))),
            ["log-4.txt"], 2,
            self.assert_reflected_output)

        clean_up()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_sing.json"),
                         "-x",
                         self.get_file_path("invocation_sing.json"),
                         "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                         "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2"))),
            ["log-4.txt"], 2,
            self.assert_reflected_output)

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_example1_crash_pull_singularity(self):
        clean_up()
        with pytest.raises(ExecutorError) as e:
            bosh.execute("launch",
                         self.get_file_path(
                             "example1_sing_crash_pull.json"),
                         self.get_file_path(
                             "invocation_sing.json"),
                         "--skip-data-collection",
                         "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                         "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2")))
        self.assertIn("Could not pull Singularity image",
                      str(e.getrepr(style='long')))

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_missing_script(self):
        clean_up()
        be = bosh.execute(
            "launch",
            self.get_file_path("example1_docker.json"),
            self.get_file_path("invocation_missing_script.json"),
            "--skip-data-collection",
            "--no-automounts",
            "-v", "{}:/test_mount1".format(
                self.get_file_path("example1_mount1")),
            "-v", "{}:/test_mount2".format(
                self.get_file_path("example1_mount2")))
        self.assert_failed_return(
            be, 2, "File does not exist!", ["log-4-pwet.txt"], 1)

    def test_example1_exec_fail_cli(self):
        clean_up()
        command = (
            "bosh", "exec", "launch",
            self.get_file_path("example1_docker.json"),
            self.get_file_path("invocation_missing_script.json"),
            "--skip-data-collection",
            "--no-automounts",
            "-v", "{}:/test_mount1".format(
                self.get_file_path("example1_mount1")),
            "-v", "{}:/test_mount2".format(
                self.get_file_path("example1_mount2")))
        command = " ".join(command)
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

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_docker_non_utf8(self):
        clean_up()
        ret = bosh.execute("launch",
                           self.get_file_path("example1_docker_nonutf8.json"),
                           self.get_file_path("invocation.json"),
                           "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                           "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2")))

        self.assert_successful_return(
            ret, ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output_nonutf8)

        clean_up()
        self.assert_successful_return(
            bosh.execute("launch",
                         self.get_file_path("example1_docker_nonutf8.json"),
                         "-x",
                         self.get_file_path("invocation.json"),
                         "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                         "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2"))),
            ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output_nonutf8)

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_example1_exec_docker_force_singularity(self):
        clean_up()
        ret = bosh.execute("launch",
                           self.get_file_path("example1_docker.json"),
                           self.get_file_path("invocation_no_opts.json"),
                           "--skip-data-collection",
                           "--force-singularity",
                           "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                           "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2")))

        self.assert_successful_return(
            ret, ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)
        self.assertIn("Local (boutiques-example1-test.simg)",
                      ret.container_location)
        self.assertIn("singularity exec", ret.container_command)

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_example1_exec_docker_Index_force_singularity(self):
        clean_up()
        ret = bosh.execute("launch",
                           self.get_file_path("example1_docker_w_index.json"),
                           self.get_file_path("invocation_no_opts.json"),
                           "--skip-data-collection",
                           "-v", "{}:/test_mount1".format(
                               self.get_file_path("example1_mount1")),
                           "-v", "{}:/test_mount2".format(
                               self.get_file_path("example1_mount2")),
                           "--force-singularity")

        self.assert_successful_return(
            ret, ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)
        self.assertIn("Local (boutiques-example1-test.simg)",
                      ret.container_location)
        self.assertIn("singularity exec", ret.container_command)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_exec_singularity_force_docker(self):
        clean_up()
        ret = bosh.execute("launch",
                           self.get_file_path("example1_sing.json"),
                           self.get_file_path("invocation_sing_no_opts.json"),
                           "--skip-data-collection",
                           "--force-docker",
                           "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                           "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2")))

        self.assert_successful_return(
            ret, ["log-4.txt"], 2,
            self.assert_reflected_output)
        self.assertIn("Local copy", ret.container_location)
        self.assertIn("docker run", ret.container_command)

    def docker_not_installed(command):
        if command == 'docker':
            return False
        else:
            return True

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    @mock.patch('boutiques.localExec.LocalExecutor._isCommandInstalled',
                side_effect=docker_not_installed)
    def test_example1_exec_docker_not_installed(self,
                                                mock_docker_not_installed):
        clean_up()
        ret = bosh.execute("launch",
                           self.get_file_path("example1_docker.json"),
                           self.get_file_path("invocation_no_opts.json"),
                           "--skip-data-collection",
                           "-v", "{}:/test_mount1".format(
                             self.get_file_path("example1_mount1")),
                           "-v", "{}:/test_mount2".format(
                             self.get_file_path("example1_mount2")))
        self.assert_successful_return(
            ret, ["log-4-coin;plop.txt"], 2,
            self.assert_reflected_output)
        self.assertIn("Local (boutiques-example1-test.simg)",
                      ret.container_location)
        self.assertIn("singularity exec", ret.container_command)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_conditional_outputFiles_created(self):
        base_path = os.path.join(self.tests_dir, "example1")
        ex = bosh.execute("launch",
                          self.get_file_path(
                              "example1_docker_conditional_outputFiles.json"),
                          self.get_file_path(
                              "example1_conditional_invoc.json"),
                          "--skip-data-collection")

        outFileList = [str(out) for out in ex.output_files]
        self.assertIn("TEST.one.three.two_out1.txt (out1, Required)",
                      outFileList)
        self.assertIn("TEST_string1.txt (out2, Required)",
                      outFileList)
        self.assertEqual([], ex.missing_files)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_environment_variables_from_invoc(self):
        ex = bosh.execute(
            "launch",
            self.get_file_path("example1_envVars_from_inputs.json"),
            self.get_file_path("test_input_env_var_invoc.json"),
            "--skip-data-collection")

        outFileList = [str(out) for out in ex.output_files]
        try:
            self.assertIn('file.txt (output_file, Required)', outFileList)
            with open(outFileList[0].split()[0]) as file:
                text = file.read()
                self.assertIn('subdir1/test_path.d', text)
        finally:
            if os.path.isfile(outFileList[0].split()[0]):
                os.remove(outFileList[0].split()[0])

    @pytest.mark.skipif(subprocess.Popen("type singularity", shell=True).wait(),
                        reason="Singularity not installed")
    def test_example1_exec_container_image_contains_index(self):
        ret = bosh.execute("launch",
                           self.get_file_path("conImage_with_index.json"),
                           self.get_file_path("input_invoc.json"),
                           "--skip-data-collection")

        self.assertIn("Local (boutiques-example1-test.simg)",
                      ret.container_location)
        self.assertIn("singularity exec", ret.container_command)
        clean_up()

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_autoMount_input_files(self):
        base_path = os.path.join(os.path.split(bfile)[0], "tests/automount/")
        test_invoc = self.get_file_path("test_automount_invoc.json")
        # Test files must be created outside of [...]/tools/python/
        # because it is mounted by default
        test_dir = "/".join(os.path.split(bfile)[0].split("/")[0:-2])
        copy2(os.path.join(base_path, "file1.txt"), test_dir)
        copy2(os.path.join(base_path, "file2.txt"), test_dir)
        copy2(os.path.join(base_path, "file3.txt"), test_dir)
        invoc_dict = {"file": test_dir + "/file1.txt",
                      "file_list": ["../file2.txt", "../file3.txt"]}
        # Create test invoc based on absolute test_dir path
        with open(test_invoc, "w+") as invoc:
            invoc.write(json.dumps(invoc_dict))

        ex = bosh.execute("launch",
                          self.get_file_path("test_automount_desc.json"),
                          test_invoc,
                          "--skip-data-collection")

        try:
            self.assertIn('Hello, World!', ex.stdout)
        finally:
            os.remove(os.path.join(test_dir, "file1.txt"))
            os.remove(os.path.join(test_dir, "file2.txt"))
            os.remove(os.path.join(test_dir, "file3.txt"))
            os.remove(test_invoc)

    @pytest.mark.skipif(subprocess.Popen("type docker", shell=True).wait(),
                        reason="Docker not installed")
    def test_example1_autoMount_none(self):
        base_path = os.path.join(os.path.split(bfile)[0], "tests/automount/")
        test_invoc = self.get_file_path("test_automount_invoc.json")
        # Test files must be created outside of [...]/tools/python/
        # because it is mounted by default
        test_dir = "/".join(os.path.split(bfile)[0].split("/")[0:-2])
        copy2(os.path.join(base_path, "file1.txt"), test_dir)
        copy2(os.path.join(base_path, "file2.txt"), test_dir)
        copy2(os.path.join(base_path, "file3.txt"), test_dir)
        invoc_dict = {"file": test_dir + "/file1.txt",
                      "file_list": ["../file2.txt", "../file3.txt"]}
        # Create test invoc based on absolute test_dir path
        with open(test_invoc, "w+") as invoc:
            invoc.write(json.dumps(invoc_dict))

        ex = bosh.execute("launch",
                          self.get_file_path("test_automount_desc.json"),
                          test_invoc,
                          "--no-automounts",
                          "--skip-data-collection")

        try:
            self.assertIn('file1.txt: No such file or directory', ex.stderr)
            self.assertIn('file2.txt: No such file or directory', ex.stderr)
            self.assertIn('file3.txt: No such file or directory', ex.stderr)
        finally:
            os.remove(os.path.join(test_dir, "file1.txt"))
            os.remove(os.path.join(test_dir, "file2.txt"))
            os.remove(os.path.join(test_dir, "file3.txt"))
            os.remove(test_invoc)

    # Captures the stdout and stderr during test execution
    # and returns them as a tuple in readouterr()
    @pytest.fixture(autouse=True)
    def capfd(self, capfd):
        self.capfd = capfd
