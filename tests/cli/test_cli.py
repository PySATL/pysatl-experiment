"""Tests for CLI command registration."""

import click
import pytest
from click.testing import CliRunner

import pysatl_experiment.cli.cli as cli_module
from pysatl_experiment.cli.commands.build_and_run import build_and_run
from pysatl_experiment.cli.commands.configure import configure
from pysatl_experiment.cli.commands.create import create
from pysatl_experiment.cli.commands.criteria import available_criteria
from pysatl_experiment.cli.commands.show import show
from pysatl_experiment.cli.shared import cli


EXPECTED_COMMANDS = {
    "available-criteria": available_criteria,
    "create": create,
    "configure": configure,
    "show": show,
    "build-and-run": build_and_run,
}


# Checks that the module exposes the same group instance as pysatl_experiment.cli.shared.
def test_module_exposes_shared_group() -> None:
    assert cli_module.cli is cli
    assert isinstance(cli, click.Group)


# Checks that exactly the expected commands are registered in the group.
def test_registered_commands_match_expected_names() -> None:
    assert set(cli.commands.keys()) == set(EXPECTED_COMMANDS.keys())
    assert len(cli.commands) == len(EXPECTED_COMMANDS)


# Checks that every expected name maps to the very command object imported from its module.
@pytest.mark.parametrize(("name", "command"), list(EXPECTED_COMMANDS.items()))
def test_expected_command_is_registered_by_identity(name: str, command: click.Command) -> None:
    assert cli.commands[name] is command
    assert isinstance(command, click.Command)


# Checks that each registered entry buildable by click exposes a working help screen.
@pytest.mark.parametrize("name", list(EXPECTED_COMMANDS.keys()))
def test_registered_command_help_screen(name: str) -> None:
    result = CliRunner().invoke(cli.commands[name], ["--help"])

    assert result.exit_code == 0
    assert "Usage:" in result.output


# Checks that the group help screen lists every registered command name.
def test_group_help_lists_all_registered_commands() -> None:
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    for name in EXPECTED_COMMANDS:
        assert name in result.output


# Checks that command names follow click's kebab-case convention.
@pytest.mark.parametrize("name", list(EXPECTED_COMMANDS.keys()))
def test_command_names_are_kebab_case(name: str) -> None:
    assert name == name.lower()
    assert "_" not in name
