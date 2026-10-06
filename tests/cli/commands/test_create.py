"""Tests for the create CLI command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.create import create


EXPECTED_DEFAULT_CONFIG = {
    "generator_type": "standard",
    "executor_type": "standard",
    "report_builder_type": "standard",
    "run_mode": "reuse",
    "report_mode": "with-chart",
    "parallel_workers": 1,
}


# Checks that creating a fresh experiment echoes the success message and persists data.
@patch("pysatl_experiment.cli.commands.create.save_experiment_data")
@patch("pysatl_experiment.cli.commands.create.is_experiment_exists", return_value=False)
def test_create_success(is_experiment_exists: MagicMock, save_experiment_data: MagicMock) -> None:
    result = CliRunner().invoke(create, ["my-exp"])

    assert result.exit_code == 0
    assert result.exception is None
    assert "Experiment with name 'my_exp' was created successfully." in result.output
    is_experiment_exists.assert_called_once_with("my_exp")
    save_experiment_data.assert_called_once()


# Checks that the persisted payload carries the experiment name and default config.
@patch("pysatl_experiment.cli.commands.create.save_experiment_data")
@patch("pysatl_experiment.cli.commands.create.is_experiment_exists", return_value=False)
def test_create_persists_default_config(is_experiment_exists: MagicMock, save_experiment_data: MagicMock) -> None:
    CliRunner().invoke(create, ["demo"])

    saved_name, saved_data = save_experiment_data.call_args.args

    assert saved_name == "demo"
    assert saved_data["name"] == "demo"
    assert saved_data["config"] == EXPECTED_DEFAULT_CONFIG


# Checks that an existing experiment aborts with an error before saving.
@patch("pysatl_experiment.cli.commands.create.save_experiment_data")
@patch("pysatl_experiment.cli.commands.create.is_experiment_exists", return_value=True)
def test_create_fails_when_experiment_exists(is_experiment_exists: MagicMock, save_experiment_data: MagicMock) -> None:
    result = CliRunner().invoke(create, ["dup"])

    assert result.exit_code != 0
    assert "already exists" in result.output
    save_experiment_data.assert_not_called()


# Checks that the name is normalized (lower-cased, spaces and dashes replaced) before use.
@pytest.mark.parametrize(
    ("raw_name", "normalized"),
    [
        ("My-Experiment", "my_experiment"),
        ("  Spaced Name  ", "spaced_name"),
        ("UPPER", "upper"),
    ],
)
@patch("pysatl_experiment.cli.commands.create.save_experiment_data")
@patch("pysatl_experiment.cli.commands.create.is_experiment_exists", return_value=False)
def test_create_normalizes_name(
    is_experiment_exists: MagicMock, save_experiment_data: MagicMock, raw_name: str, normalized: str
) -> None:
    result = CliRunner().invoke(create, [raw_name])

    assert result.exit_code == 0
    is_experiment_exists.assert_called_once_with(normalized)
    assert save_experiment_data.call_args.args[0] == normalized
