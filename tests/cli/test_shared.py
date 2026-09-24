"""Tests for the shared CLI application instance."""

from unittest.mock import patch

import click
from click.testing import CliRunner

from pysatl_experiment.cli.shared import cli


def probe_callback() -> None:
    """No-op callback used to observe the group callback side effects."""


# Checks that the module exposes a click group named cli.
def test_cli_is_a_click_group_named_cli() -> None:
    assert isinstance(cli, click.Group)
    assert cli.name == "cli"


# Checks that the group help screen shows the application description and options.
def test_group_help_describes_application() -> None:
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "PySATL experiments command-line interface." in result.output
    assert "--version" in result.output
    assert "--help" in result.output


# Checks that the version option is registered and reports a version string.
def test_version_option_reports_version() -> None:
    result = CliRunner().invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert result.output.startswith("cli, version ")
    assert result.output.strip() != "cli, version"


# Checks that invoking a subcommand runs ensure_experiment_dir from the group callback.
def test_group_callback_ensures_experiment_dir() -> None:
    cli.add_command(click.Command("probe", callback=probe_callback))
    try:
        with patch("pysatl_experiment.cli.shared.ensure_experiment_dir") as ensure_experiment_dir:
            result = CliRunner().invoke(cli, ["probe"])
    finally:
        cli.commands.pop("probe", None)

    assert result.exit_code == 0
    assert result.exception is None
    assert "probe" not in cli.commands
    ensure_experiment_dir.assert_called_once_with()


# Checks that the eager --help option resolves before the group callback side effect.
def test_help_option_does_not_trigger_group_callback() -> None:
    with patch("pysatl_experiment.cli.shared.ensure_experiment_dir") as ensure_experiment_dir:
        result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    ensure_experiment_dir.assert_not_called()


# Checks that an unknown command fails during resolution and skips the group callback.
def test_unknown_command_does_not_trigger_group_callback() -> None:
    with patch("pysatl_experiment.cli.shared.ensure_experiment_dir") as ensure_experiment_dir:
        result = CliRunner().invoke(cli, ["unknown-command"])

    assert result.exit_code != 0
    ensure_experiment_dir.assert_not_called()
