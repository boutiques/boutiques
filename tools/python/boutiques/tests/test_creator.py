#!/usr/bin/env python

from unittest import TestCase
from boutiques.bosh import bosh
from boutiques import __file__ as bfile
import subprocess
import os.path as op
import os


class TestCreator(TestCase):

    def test_success(self):
        fil = 'creator_output.json'
        bosh(['create', fil])
        assert bosh(['validate', fil]) is None
