#!/usr/bin/env python

from boutiques import bosh
from unittest import TestCase
from os.path import join as opj
from boutiques import __file__ as bfile
import pytest
import boutiques
import subprocess
import os.path as op
import simplejson as json


class TestOutputFiles(TestCase):

    @pytest.fixture(scope='session', autouse=True)
    def clean_up(self):
        yield
        # os.remove("user-image.simg")

    def test_output_conditional_names(self):
        base_path = op.join(op.split(bfile)[0], "tests/output_files/")
        test_desc = op.join(base_path, "test_fixedANDcond_output.json")
        test_invoc = op.join(base_path, "test_fixedANDcond_output_invoc.json")
        output_file_names = op.join(base_path, "test_fileNames.json")

        # Checks validator
        launch_args = ["example", test_desc, "-c"]
        bosh(launch_args)

        # Make it fail validator

        # Checks conditions are respected
        launch_args = ["exec", "launch", test_desc, test_invoc]
        # look for expected outputfiles
        bosh(launch_args)
