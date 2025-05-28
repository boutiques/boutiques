#!/usr/bin/env python

import os
import subprocess
from pathlib import Path
from shutil import copy2
from unittest import mock

import pytest
import simplejson as json
from boutiques_mocks import example_boutiques_tool, mock_get

import boutiques as bosh
from boutiques import __file__ as bfile
from boutiques.descriptor2func import function
from boutiques.localExec import ExecutorError
from boutiques.tests.BaseTest import BaseTest
from boutiques.util.utils import LoadError


class TestExample1(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("example1")

    @pytest.fixture(autouse=True)
    def clean_up(self):
        fls = os.listdir("./")
        for fl in fls:
            if (fl.startswith("log") or fl.startswith("config")) and fl.endswith(
                ".txt"
            ):
                os.remove(fl)

    # Captures the stdout and stderr during test execution
    # and returns them as a tuple in readouterr()
    @pytest.fixture(autouse=True)
    def capture_st(self, capfd):
        self.capfd = capfd

    def test_example1_validate(self):
        self.assertIsNone(bosh.validate(self.example1_descriptor))

    def test_example1_no_exec(self):
        invoc = os.path.join(
            os.path.dirname(bfile),
            "schema",
            "examples",
            "example1",
            "invocation.json",
        )
        self.assert_successful_return(
            bosh.execute("simulate", self.example1_descriptor, "-i", invoc),
            aditional_assertions=self.assert_only_stdout,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_exec_docker(self):
        invoc = os.path.join(
            os.path.dirname(bfile),
            "schema",
            "examples",
            "example1",
            "invocation.json",
        )
        ret = bosh.execute(
            "launch",
            self.example1_descriptor,
            invoc,
            "--skip-data-collection",
            "-v",
            f"{self.get_file_path('example1_mount1')}:/test_mount1",
            "-v",
            f"{self.get_file_path('example1_mount2')}:/test_mount2",
        )

        # Make sure stdout and stderr are not printed on the fly
        # for non-streaming mode
        out, err = self.capfd.readouterr()
        self.assertNotIn("This is stdout", out)
        self.assertNotIn("This is stderr", err)

        self.assert_successful_return(
            ret,
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_exec_docker_debug(self):
        invoc = os.path.join(
            os.path.dirname(bfile),
            "schema",
            "examples",
            "example1",
            "invocation.json",
        )
        self.assert_successful_return(
            bosh.execute(
                "launch",
                self.example1_descriptor,
                "--debug",
                invoc,
                "--skip-data-collection",
                "-v",
                f"{self.get_file_path('example1_mount1')}:/test_mount1",
                "-v",
                f"{self.get_file_path('example1_mount2')}:/test_mount2",
            ),
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_exec_docker_stream_output(self):
        invoc = os.path.join(
            os.path.dirname(bfile),
            "schema",
            "examples",
            "example1",
            "invocation.json",
        )
        ret = bosh.execute(
            "launch",
            self.example1_descriptor,
            "-s",
            invoc,
            "--skip-data-collection",
            "-v",
            f"{self.get_file_path('example1_mount1')}:/test_mount1",
            "-v",
            f"{self.get_file_path('example1_mount2')}:/test_mount2",
        )

        # Make sure stdout and stderr are printed on the fly for
        # streaming mode
        out, _ = self.capfd.readouterr()
        self.assertIn("This is stdout", out)
        self.assertIn("This is stderr", out)

        self.assertIsNone(ret.stdout)
        self.assertIsNone(ret.stderr)

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_exec_docker_inv_as_json_obj(self):
        invocationStr = open(
            os.path.join(
                os.path.dirname(bfile),
                "schema",
                "examples",
                "example1",
                "invocation.json",
            )
        ).read()
        self.assert_successful_return(
            bosh.execute(
                "launch",
                self.example1_descriptor,
                invocationStr,
                "--skip-data-collection",
                "-v",
                f"{self.get_file_path('example1_mount1')}:/test_mount1",
                "-v",
                f"{self.get_file_path('example1_mount2')}:/test_mount2",
            ),
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_exec_docker_inv_as_json_obj_debug(self):
        invoc = os.path.join(
            os.path.dirname(bfile),
            "schema",
            "examples",
            "example1",
            "invocation.json",
        )
        self.assert_successful_return(
            bosh.execute(
                "launch",
                self.example1_descriptor,
                "--debug",
                invoc,
                "-v",
                f"{self.get_file_path('example1_mount1')}:/test_mount1",
                "-v",
                f"{self.get_file_path('example1_mount2')}:/test_mount2",
                "--skip-data-collection",
            ),
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_exec_docker_desc_as_json_obj(self):
        descStr = open(self.example1_descriptor).read()
        invoc = os.path.join(
            os.path.dirname(bfile),
            "schema",
            "examples",
            "example1",
            "invocation.json",
        )
        self.assert_successful_return(
            bosh.execute(
                "launch",
                descStr,
                invoc,
                "--skip-data-collection",
                "-v",
                f"{self.get_file_path('example1_mount1')}:/test_mount1",
                "-v",
                f"{self.get_file_path('example1_mount2')}:/test_mount2",
            ),
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_exec_docker_desc_as_json_obj_debug(self):
        descStr = open(self.example1_descriptor).read()
        invoc = os.path.join(
            os.path.dirname(bfile),
            "schema",
            "examples",
            "example1",
            "invocation.json",
        )
        self.assert_successful_return(
            bosh.execute(
                "launch",
                descStr,
                invoc,
                "--debug",
                "--skip-data-collection",
                "-v",
                f"{self.get_file_path('example1_mount1')}:/test_mount1",
                "-v",
                f"{self.get_file_path('example1_mount2')}:/test_mount2",
            ),
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_exec_docker_json_string_invalid(self):
        invocationStr = open(self.get_file_path("invocation_invalid.json")).read()
        with pytest.raises(LoadError) as e:
            bosh.execute(
                "launch",
                self.example1_descriptor,
                "-u",
                invocationStr,
                "--skip-data-collection",
            )
        self.assertIn("Cannot parse input", str(e.getrepr(style="long")))

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    @mock.patch("requests.get", return_value=mock_get())
    def test_example1_exec_docker_from_zenodo(self, _):
        invoc = os.path.join(
            os.path.dirname(bfile),
            "schema",
            "examples",
            "example1",
            "invocation.json",
        )
        ret = bosh.execute(
            "launch",
            "zenodo." + str(example_boutiques_tool.id),
            invoc,
            "--skip-data-collection",
            "-v",
            f"{self.get_file_path('example1_mount1')}:/test_mount1",
            "-v",
            f"{self.get_file_path('example1_mount2')}:/test_mount2",
        )

        # Make sure stdout and stderr are not printed on the fly
        # for non-streaming mode
        out, err = self.capfd.readouterr()
        self.assertNotIn("This is stdout", out)
        self.assertNotIn("This is stderr", err)
        self.assert_successful_return(
            ret,
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    @mock.patch("requests.get", return_value=mock_get())
    def test_example1_exec_docker_from_zenodo_debug(self, _):
        invoc = os.path.join(
            os.path.dirname(bfile),
            "schema",
            "examples",
            "example1",
            "invocation.json",
        )
        self.assert_successful_return(
            bosh.execute(
                "launch",
                "zenodo." + str(example_boutiques_tool.id),
                "--debug",
                invoc,
                "--skip-data-collection",
                "-v",
                f"{self.get_file_path('example1_mount1')}:/test_mount1",
                "-v",
                f"{self.get_file_path('example1_mount2')}:/test_mount2",
            ),
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    @mock.patch("requests.get", return_value=mock_get())
    def test_example1_exec_docker_from_zenodo_desc2func_default(self, _):
        # No mode provided, defaults to 'launch'
        example_tool = function("zenodo." + str(example_boutiques_tool.id))
        ret = example_tool(
            str_input_list=["a", "b", "c"],
            str_input="coin;plop",
            file_input="./pyproject.toml",
            file_list_input=["./pyproject.toml"],
            list_int_input=[1, 2, 3],
            config_num=4,
            enum_input="val1",
        )
        self.assert_successful_return(
            ret,
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    @mock.patch("requests.get", return_value=mock_get())
    def test_example1_exec_docker_from_zenodo_desc2func_launch(self, _):
        # Launch mode
        example_tool = function("zenodo." + str(example_boutiques_tool.id))
        ret = example_tool(
            "launch",
            str_input_list=["a", "b", "c"],
            str_input="coin;plop",
            file_input="./pyproject.toml",
            file_list_input=["./pyproject.toml"],
            list_int_input=[1, 2, 3],
            config_num=4,
            enum_input="val1",
        )
        self.assert_successful_return(
            ret,
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    @mock.patch("requests.get", return_value=mock_get())
    def test_example1_exec_docker_from_zenodo_desc2func_simulate(self, _):
        # Simulate with invocation
        example_tool = function("zenodo." + str(example_boutiques_tool.id))
        ret = example_tool(
            "simulate",
            str_input_list=["a", "b", "c"],
            str_input="coin;plop",
            file_input="./pyproject.toml",
            file_list_input=["./pyproject.toml"],
            list_int_input=[1, 2, 3],
            config_num=4,
            enum_input="val1",
        )
        self.assert_successful_return(ret, aditional_assertions=self.assert_only_stdout)

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    @mock.patch("requests.get", return_value=mock_get())
    def test_example1_exec_docker_from_zenodo_desc2func_simNoInvoc(self, _):
        # Simulate without invocation
        example_tool = function("zenodo." + str(example_boutiques_tool.id))
        ret = example_tool("simulate")
        self.assertIn("exampleTool1.py -c", ret.stdout)

    @pytest.mark.xfail(reason="Travis to GH action transition")
    @pytest.mark.skipif(
        subprocess.Popen("type singularity", shell=True).wait(),
        reason="Singularity not installed",
    )
    def test_example1_exec_singularity(self):
        self.assert_successful_return(
            bosh.execute(
                "launch",
                self.get_file_path("example1_sing.json"),
                self.get_file_path("invocation_sing.json"),
                "--skip-data-collection",
                "-v",
                f"{self.get_file_path('example1_mount1')}:/test_mount1",
                "-v",
                f"{self.get_file_path('example1_mount2')}:/test_mount2",
            ),
            ["./test_temp/log-4.txt"],
            2,
            self.assert_reflected_output,
        )

    @pytest.mark.xfail(reason="Travis to GH action transition")
    @pytest.mark.skipif(
        subprocess.Popen("type singularity", shell=True).wait(),
        reason="Singularity not installed",
    )
    def test_example1_exec_singularity_debug(self):
        self.assert_successful_return(
            bosh.execute(
                "launch",
                self.get_file_path("example1_sing.json"),
                "--debug",
                self.get_file_path("invocation_sing.json"),
                "-v",
                f"{self.get_file_path('example1_mount1')}:/test_mount1",
                "-v",
                f"{self.get_file_path('example1_mount2')}:/test_mount2",
            ),
            ["./test_temp/log-4.txt"],
            2,
            self.assert_reflected_output,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type singularity", shell=True).wait(),
        reason="Singularity not installed",
    )
    def test_example1_crash_pull_singularity(self):
        with pytest.raises(ExecutorError) as e:
            bosh.execute(
                "launch",
                self.get_file_path("example1_sing_crash_pull.json"),
                self.get_file_path("invocation_sing.json"),
                "--skip-data-collection",
                "-v",
                f"{self.get_file_path('example1_mount1')}:/test_mount1",
                "-v",
                f"{self.get_file_path('example1_mount2')}:/test_mount2",
            )
        self.assertIn("Could not pull Singularity image", str(e.getrepr(style="long")))

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_exec_missing_script(self):
        be = bosh.execute(
            "launch",
            self.example1_descriptor,
            self.get_file_path("invocation_missing_script.json"),
            "--skip-data-collection",
            "--no-automounts",
            "-v",
            f"{self.get_file_path('example1_mount1')}:/test_mount1",
            "-v",
            f"{self.get_file_path('example1_mount2')}:/test_mount2",
        )
        self.assert_failed_return(
            be, 2, "File does not exist!", ["./test_temp/log-4-pwet.txt"], 1
        )

    @pytest.mark.skip(reason="Fails after transition to GH action")
    def test_example1_exec_fail_cli(self):
        command = (
            "bosh",
            "exec",
            "launch",
            self.example1_descriptor,
            self.get_file_path("invocation_missing_script.json"),
            "--skip-data-collection",
            "--no-automounts",
            "-v",
            f"{self.get_file_path('example1_mount1')}:/test_mount1",
            "-v",
            f"{self.get_file_path('example1_mount2')}:/test_mount2",
        )
        command = " ".join(command)
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        process.communicate()
        assert process.returncode == 2, command

    def test_example1_no_exec_random(self):
        self.assert_successful_return(
            bosh.execute("simulate", self.example1_descriptor),
            aditional_assertions=self.assert_only_stdout,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_exec_docker_non_utf8(self):
        invoc = os.path.join(
            os.path.dirname(bfile),
            "schema",
            "examples",
            "example1",
            "invocation.json",
        )
        ret = bosh.execute(
            "launch",
            self.get_file_path("example1_docker_nonutf8.json"),
            invoc,
            "-v",
            f"{self.get_file_path('example1_mount1')}:/test_mount1",
            "-v",
            f"{self.get_file_path('example1_mount2')}:/test_mount2",
        )

        self.assert_successful_return(
            ret,
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output_nonutf8,
        )

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_exec_docker_non_utf8_debug(self):
        invoc = os.path.join(
            os.path.dirname(bfile),
            "schema",
            "examples",
            "example1",
            "invocation.json",
        )
        self.assert_successful_return(
            bosh.execute(
                "launch",
                self.get_file_path("example1_docker_nonutf8.json"),
                "--debug",
                invoc,
                "-v",
                f"{self.get_file_path('example1_mount1')}:/test_mount1",
                "-v",
                f"{self.get_file_path('example1_mount2')}:/test_mount2",
            ),
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output_nonutf8,
        )

    @pytest.mark.xfail(reason="Travis to GH action transition")
    @pytest.mark.skipif(
        subprocess.Popen("type singularity", shell=True).wait(),
        reason="Singularity not installed",
    )
    def test_example1_exec_docker_force_singularity(self):
        ret = bosh.execute(
            "launch",
            self.example1_descriptor,
            self.get_file_path("invocation_no_opts.json"),
            "--skip-data-collection",
            "--force-singularity",
            "-v",
            f"{self.get_file_path('example1_mount1')}:/test_mount1",
            "-v",
            f"{self.get_file_path('example1_mount2')}:/test_mount2",
        )

        self.assert_successful_return(
            ret,
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )
        self.assertIn("Local (boutiques-example1-test.simg)", ret.container_location)
        self.assertIn("singularity exec", ret.container_command)

    @pytest.mark.xfail(reason="Travis to GH action transition")
    @pytest.mark.skipif(
        subprocess.Popen("type singularity", shell=True).wait(),
        reason="Singularity not installed",
    )
    def test_example1_exec_docker_Index_force_singularity(self):
        ret = bosh.execute(
            "launch",
            self.get_file_path("example1_docker_w_index.json"),
            self.get_file_path("invocation_no_opts.json"),
            "--skip-data-collection",
            "-v",
            f"{self.get_file_path('example1_mount1')}:/test_mount1",
            "-v",
            f"{self.get_file_path('example1_mount2')}:/test_mount2",
            "--force-singularity",
        )

        self.assert_successful_return(
            ret,
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )
        self.assertIn("Local (boutiques-example1-test.simg)", ret.container_location)
        self.assertIn("singularity exec", ret.container_command)

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_exec_singularity_force_docker(self):
        ret = bosh.execute(
            "launch",
            self.get_file_path("example1_sing.json"),
            self.get_file_path("invocation_sing_no_opts.json"),
            "--skip-data-collection",
            "--force-docker",
            "-v",
            f"{self.get_file_path('example1_mount1')}:/test_mount1",
            "-v",
            f"{self.get_file_path('example1_mount2')}:/test_mount2",
        )

        self.assert_successful_return(
            ret, ["./test_temp/log-4.txt"], 2, self.assert_reflected_output
        )
        self.assertIn("Pulled from Docker", ret.container_location)
        self.assertIn("docker run", ret.container_command)

    def docker_not_installed(command):
        if command == "docker":
            return False
        else:
            return True

    @pytest.mark.xfail(reason="Travis to GH action transition")
    @pytest.mark.skipif(
        subprocess.Popen("type singularity", shell=True).wait(),
        reason="Singularity not installed",
    )
    @mock.patch(
        "boutiques.localExec.LocalExecutor._isCommandInstalled",
        side_effect=docker_not_installed,
    )
    def test_example1_exec_docker_not_installed(self, mock_docker_not_installed):
        ret = bosh.execute(
            "launch",
            self.example1_descriptor,
            self.get_file_path("invocation_no_opts.json"),
            "--skip-data-collection",
            "-v",
            f"{self.get_file_path('example1_mount1')}:/test_mount1",
            "-v",
            f"{self.get_file_path('example1_mount2')}:/test_mount2",
        )
        self.assert_successful_return(
            ret,
            ["./test_temp/log-4-coin;plop.txt"],
            2,
            self.assert_reflected_output,
        )
        self.assertIn("Local (boutiques-example1-test.simg)", ret.container_location)
        self.assertIn("singularity exec", ret.container_command)

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_conditional_outputFiles_created(self):
        os.makedirs(self.test_temp, exist_ok=True)
        ex = bosh.execute(
            "launch",
            self.get_file_path("example1_docker_conditional_outputFiles.json"),
            self.get_file_path("example1_conditional_invoc.json"),
            "--skip-data-collection",
        )

        outFileList = [str(out) for out in ex.output_files]
        self.assertIn(
            "./test_temp/TEST.one.three.two_out1.txt" " (out1, Required)",
            outFileList,
        )
        self.assertIn("./test_temp/TEST_string1.txt (out2, Required)", outFileList)
        self.assertEqual([], ex.missing_files)

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_environment_variables_from_invoc(self):
        Path(self.test_temp, "test_path.d").touch()
        ex = bosh.execute(
            "launch",
            self.get_file_path("example1_envVars_from_inputs.json"),
            self.get_file_path("test_input_env_var_invoc.json"),
            "--skip-data-collection",
        )

        self.assertIn("./test_temp/test_path.d", ex.stdout)

    @pytest.mark.usefixtures("skip_if_no_docker")
    def test_missing_mount_location(self):
        from boutiques.localExec import ExecutorError

        with pytest.raises(ExecutorError):
            bosh.execute(
                "launch",
                self.get_file_path("example1_envVars_from_inputs.json"),
                self.get_file_path("test_input_env_var_invoc.json"),
                "--skip-data-collection",
            )

    @pytest.mark.skipif(
        subprocess.Popen("type singularity", shell=True).wait(),
        reason="Singularity not installed",
    )
    def test_example1_exec_container_image_contains_index(self):
        ret = bosh.execute(
            "launch",
            self.get_file_path("conImage_with_index.json"),
            self.get_file_path("input_invoc.json"),
            "--skip-data-collection",
        )

        self.assertIn("Local (boutiques-example1-test.simg)", ret.container_location)
        self.assertIn("singularity exec", ret.container_command)

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_autoMount_input_files(self):
        base_path = self.get_file_path("automount")
        # Test files must be created outside of [...]/tools/python/
        # because it is mounted by default
        test_dir = os.path.split(os.path.split(bfile)[0])[0]
        copy2(os.path.join(base_path, "file1.txt"), test_dir)
        copy2(os.path.join(base_path, "file2.txt"), test_dir)
        copy2(os.path.join(base_path, "file3.txt"), test_dir)
        # copy2(os.path.join(test_invoc), test_dir)
        invoc_dict = {
            "file": "./file1.txt",
            "file_list": ["./file2.txt", "./file3.txt"],
        }
        # Create test invoc based on absolute test_dir path
        test_invoc = self.get_file_path("test_automount_invoc.json")
        with open(test_invoc, "w+") as invoc:
            invoc.write(json.dumps(invoc_dict))

        ex = bosh.execute(
            "launch",
            self.get_file_path("test_automount_desc.json"),
            test_invoc,
            "--skip-data-collection",
        )

        try:
            self.assertIn("Hello, World!", ex.stdout.replace("\n", ""))
        finally:
            os.remove(os.path.join(test_dir, "file1.txt"))
            os.remove(os.path.join(test_dir, "file2.txt"))
            os.remove(os.path.join(test_dir, "file3.txt"))
            os.remove(test_invoc)

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_autoMount_none(self):
        base_path = self.get_file_path("automount")
        test_invoc = self.get_file_path("test_automount_invoc.json")
        # Test files must be created outside of [...]/tools/python/
        # because it is mounted by default
        test_dir = os.path.split(os.path.split(bfile)[0])[0]
        copy2(os.path.join(base_path, "file1.txt"), test_dir)
        copy2(os.path.join(base_path, "file2.txt"), test_dir)
        copy2(os.path.join(base_path, "file3.txt"), test_dir)
        invoc_dict = {
            "file": test_dir + "./file1.txt",
            "file_list": [test_dir + "./file2.txt", test_dir + "./file3.txt"],
        }
        # Create test invoc based on absolute test_dir path
        with open(test_invoc, "w+") as invoc:
            invoc.write(json.dumps(invoc_dict))

        ex = bosh.execute(
            "launch",
            self.get_file_path("test_automount_desc.json"),
            test_invoc,
            "--no-automounts",
            "--skip-data-collection",
        )

        try:
            self.assertIn("file1.txt: No such file or directory", ex.stderr)
            self.assertIn("file2.txt: No such file or directory", ex.stderr)
            self.assertIn("file3.txt: No such file or directory", ex.stderr)
        finally:
            os.remove(os.path.join(test_dir, "file1.txt"))
            os.remove(os.path.join(test_dir, "file2.txt"))
            os.remove(os.path.join(test_dir, "file3.txt"))
            os.remove(test_invoc)

    @pytest.mark.skipif(
        subprocess.Popen("type docker", shell=True).wait(),
        reason="Docker not installed",
    )
    def test_example1_container_opts(self):
        container_opts = "-e TEST_CONTAINER_OPTS=TEST_CONTAINER_OPTS"
        extra_container_opts = "-p 8888:8888 -e MORE_ENV=MORE_ENV"

        invoc = os.path.join(
            os.path.dirname(bfile),
            "schema",
            "examples",
            "example1",
            "invocation.json",
        )
        ret = bosh.execute(
            "launch",
            self.example1_descriptor,
            invoc,
            "--skip-data-collection",
            "-v",
            f"{self.get_file_path('example1_mount1')}:/test_mount1",
            "-v",
            f"{self.get_file_path('example1_mount2')}:/test_mount2",
            "--container-opts",
            container_opts,
            "--container-opts",
            extra_container_opts,
        )

        self.assertIn(container_opts, ret.container_command)
        self.assertIn(extra_container_opts, ret.container_command)

    @pytest.mark.xfail(reason="Travis to GH action transition")
    @pytest.mark.skipif(
        subprocess.Popen("type singularity", shell=True).wait(),
        reason="Singularity not installed",
    )
    def test_example1_singularity_container_opts(self):
        # check that container runtime options are not ignored when specified on
        # command-line, and the container runtime differs from the descriptor
        container_opts = "--cpus 1"

        ret = bosh.execute(
            "launch",
            self.example1_descriptor,
            self.get_file_path("invocation_no_opts.json"),
            "--skip-data-collection",
            "-v",
            f"{self.get_file_path('example1_mount1')}:/test_mount1",
            "-v",
            f"{self.get_file_path('example1_mount2')}:/test_mount2",
            "--force-singularity",
            "--container-opts",
            container_opts,
        )

        self.assertIn(container_opts, ret.container_command)
