#!/usr/bin/env python

"""Tests for Styx schema extensions support."""

import pytest

from boutiques.bosh import bosh
from boutiques.tests.BaseTest import BaseTest


class TestStyx(BaseTest):
    @pytest.fixture(autouse=True)
    def set_test_dir(self):
        self.setup("styx")

    def test_styx_descriptor_validates(self):
        """Test that a valid Styx descriptor passes validation."""
        fil = self.get_file_path("example_styx.json")
        self.assertIsNone(bosh(["validate", fil]))

    def test_styx_schema_version(self):
        """Test that schema-version 0.5+styx is accepted."""
        fil = self.get_file_path("example_styx.json")
        # Should not raise
        bosh(["validate", fil])

    def test_styx_nested_input_type(self):
        """Test that nested input types are accepted."""
        # The example_styx.json has a nested type for the 'config' input
        fil = self.get_file_path("example_styx.json")
        self.assertIsNone(bosh(["validate", fil]))

    def test_styx_stdout_output(self):
        """Test that stdout-output field is accepted."""
        # The example_styx.json has a stdout-output field
        fil = self.get_file_path("example_styx.json")
        self.assertIsNone(bosh(["validate", fil]))

    def test_styx_resolve_parent(self):
        """Test that resolve-parent field on inputs is accepted."""
        # The example_styx.json has resolve-parent: true on topup_result input
        fil = self.get_file_path("example_styx.json")
        self.assertIsNone(bosh(["validate", fil]))

    def test_styx_nested_type_conditional_path_template(self):
        """Test validation of conditional path templates with nested input types.

        This tests the getInputTypeName helper function's handling of nested
        types (dict) in conditional path template validation.
        """
        fil = self.get_file_path("styx_conditional_nested_type.json")
        # Should validate without error - nested types are treated as String
        self.assertIsNone(bosh(["validate", fil]))
