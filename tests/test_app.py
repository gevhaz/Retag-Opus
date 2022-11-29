"""Tests for app.py and cli.py."""
from unittest import TestCase

import pytest

from retag_opus import app


class TestApp(TestCase):
    """Tests for the main function run() of the app."""

    @pytest.fixture(autouse=True)
    def capsys(self, capsys) -> None:  # type: ignore
        """Fixture for capturing system output."""
        self.capsys = capsys  # type: ignore

    def test_print_version(self) -> None:
        """Test printing version."""
        with self.assertRaises(SystemExit):
            app.run(["--version"])
        captured = self.capsys.readouterr()  # type: ignore
        self.assertRegex(captured.out, r"^retag \(version 0.3.0\)$")

    def test_print_help(self) -> None:
        """Test printing help."""
        with self.assertRaises(SystemExit):
            app.run(["--help"])
        captured = self.capsys.readouterr()  # type: ignore
        self.assertRegex(captured.out, r"^usage:.*")
