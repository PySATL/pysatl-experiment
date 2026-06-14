"""Tests for CLI entrypoint module."""

import subprocess
import sys

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.cli import cli


class TestCliEntrypoint:
    """Basic tests for CLI entrypoint."""

    @pytest.fixture
    def runner(self):
        """Create a Click CLI runner for testing."""
        return CliRunner()

    def test_cli_imports_successfully(self):
        """Test that cli object can be imported."""
        from pysatl_experiment.cli.cli import cli

        assert cli is not None
        assert callable(cli)

    def test_cli_help_works(self, runner):
        """Test that main CLI shows help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Commands:" in result.output

    def test_python_m_execution(self):
        """Test that `python -m pysatl_experiment.cli` works."""
        result = subprocess.run(
            [sys.executable, "-m", "pysatl_experiment.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout or "Commands:" in result.stdout

    def test_entrypoint_docstring(self):
        """Test that entrypoint module has documentation."""
        import pysatl_experiment.cli.__main__ as entrypoint

        assert entrypoint.__doc__ is not None
        assert len(entrypoint.__doc__) > 0

    def test_cli_handles_no_command(self, runner):
        """Test CLI shows help when no command is given."""
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        # Click should show help or available commands
        assert len(result.output) > 0

    def test_cli_handles_invalid_command(self, runner):
        """Test CLI handles invalid commands gracefully."""
        result = runner.invoke(cli, ["nonexistent-command-xyz"])
        assert result.exit_code != 0
