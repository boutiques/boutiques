#!/usr/bin/env python

import os
import os.path as op
import subprocess
from boutiques import __file__ as bfile
import boutiques
from boutiques.tests.BaseTest import BaseTest


class TestBoutiquesTools(BaseTest):

    def test_python_interface_validate(self):
        self.setup("invocation")
        fil = self.get_file_path('good.json')
        self.assertIsNone(boutiques.validate(fil))
