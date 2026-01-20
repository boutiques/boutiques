#!/usr/bin/env python

import os

import pytest

import boutiques as bosh
from boutiques.localExec import ExecutorError
from boutiques.tests.BaseTest import BaseTest


class TestExec(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("exec")

    def test_failing_launch(self):
        self.assertRaises(
            ExecutorError,
            bosh.execute,
            (
                "launch",
                self.get_file_path("fake.json"),
                self.get_file_path("test_baremetal_invoc.json"),
                "--skip-data-collection",
            ),
        )
        self.assertRaises(
            ExecutorError,
            bosh.execute,
            (
                "launch",
                self.get_file_path("test_baremetal.json"),
                self.get_file_path("fake.json"),
                "--skip-data-collection",
            ),
        )
        self.assertRaises(
            ExecutorError,
            bosh.execute,
            (
                "launch",
                self.get_file_path("test_baremetal.json"),
                self.get_file_path("../boutiques_mocks.py"),
                "--skip-data-collection",
            ),
        )

    def test_no_container(self):
        self.assertFalse(
            bosh.execute(
                "launch",
                self.get_file_path("no_container.json"),
                self.get_file_path("no_container_invocation.json"),
                "--skip-data-collection",
            ).exit_code
        )

    def test_bare_metal_execution(self):
        e = bosh.execute(
            "launch",
            "--no-container",
            self.get_file_path("test_baremetal.json"),
            self.get_file_path("test_baremetal_invoc.json"),
        )
        stdout = e.stdout
        if os.path.exists("test_baremetal_exec.txt"):
            os.remove("test_baremetal_exec.txt")
        self.assertEqual(stdout, "Bare metal execution\n")
