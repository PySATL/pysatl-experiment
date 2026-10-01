"""Tests for the show CLI command."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.show import show


# Checks that the experiment payload is printed as indented JSON.
@patch("pysatl_experiment.cli.commands.show.read_experiment_data")
def test_show_prints_experiment_data_as_json(read_experiment_data: MagicMock) -> None:
    read_experiment_data.return_value = {"config": {"hypothesis": "normal"}, "steps": []}

    result = CliRunner().invoke(show, ["my-exp"])

    assert result.exit_code == 0
    assert result.exception is None
    assert json.loads(result.output) == {"config": {"hypothesis": "normal"}, "steps": []}
    read_experiment_data.assert_called_once_with("my-exp")


# Checks that the output uses the four-space indentation of json.dumps.
@patch("pysatl_experiment.cli.commands.show.read_experiment_data")
def test_show_uses_indented_json_output(read_experiment_data: MagicMock) -> None:
    read_experiment_data.return_value = {"a": 1}

    result = CliRunner().invoke(show, ["my-exp"])

    assert result.output.startswith('{\n    "a": 1\n}')
    assert result.output == json.dumps({"a": 1}, indent=4) + "\n"


# Checks that an empty experiment payload is printed as an empty object.
@patch("pysatl_experiment.cli.commands.show.read_experiment_data")
def test_show_handles_empty_payload(read_experiment_data: MagicMock) -> None:
    read_experiment_data.return_value = {}

    result = CliRunner().invoke(show, ["my-exp"])

    assert result.exit_code == 0
    assert json.loads(result.output) == {}


# Checks that a None payload is printed as JSON null.
@patch("pysatl_experiment.cli.commands.show.read_experiment_data")
def test_show_handles_none_payload(read_experiment_data: MagicMock) -> None:
    read_experiment_data.return_value = None

    result = CliRunner().invoke(show, ["my-exp"])

    assert result.exit_code == 0
    assert json.loads(result.output) is None


# Checks that a read failure propagates as a command error.
@patch("pysatl_experiment.cli.commands.show.read_experiment_data")
def test_show_propagates_read_failure(read_experiment_data: MagicMock) -> None:
    read_experiment_data.side_effect = FileNotFoundError("missing experiment")

    result = CliRunner().invoke(show, ["my-exp"])

    assert result.exit_code == 1
    assert isinstance(result.exception, FileNotFoundError)


# Checks that a non-serializable payload surfaces a JSON encoding error.
@patch("pysatl_experiment.cli.commands.show.read_experiment_data")
def test_show_fails_for_non_serializable_payload(read_experiment_data: MagicMock) -> None:
    read_experiment_data.return_value = {"value": object()}

    result = CliRunner().invoke(show, ["my-exp"])

    assert result.exit_code == 1
    assert isinstance(result.exception, TypeError)


# Checks that the experiment name argument is mandatory.
def test_show_requires_experiment_name() -> None:
    result = CliRunner().invoke(show, [])

    assert result.exit_code == 2
    assert "Missing argument" in result.output


# Checks that the experiment name is passed through verbatim.
@pytest.mark.parametrize("name", ["my-exp", "exp with spaces", "UPPER-Case_1"])
@patch("pysatl_experiment.cli.commands.show.read_experiment_data")
def test_show_forwards_experiment_name(read_experiment_data: MagicMock, name: str) -> None:
    read_experiment_data.return_value = {"name": name}

    result = CliRunner().invoke(show, [name])

    assert result.exit_code == 0
    read_experiment_data.assert_called_once_with(name)
