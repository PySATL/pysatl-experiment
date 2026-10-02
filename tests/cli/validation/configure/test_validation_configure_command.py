"""Tests for the command-level guards of the configure command."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure import configure


BASE_ARGS = ["-con", "sqlite:///db.sqlite", "-s", "23", "-c", "154", "-h", "normal", "-expt", "power"]


# Checks that the command refuses to configure an experiment that does not exist.
@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=False)
def test_configure_fails_for_unknown_experiment(
    is_experiment_exists: MagicMock, save_experiment_config: MagicMock
) -> None:
    result = CliRunner().invoke(configure, ["my-exp", *BASE_ARGS])

    assert result.exit_code != 0
    assert "Experiment with name my-exp does not exist." in result.output
    is_experiment_exists.assert_called_once_with("my-exp")
    save_experiment_config.assert_not_called()


# Checks that the command reports a custom generator type as unsupported.
@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
def test_configure_rejects_custom_generator_type(
    is_experiment_exists: MagicMock, read_experiment_data: MagicMock, save_experiment_config: MagicMock
) -> None:
    read_experiment_data.return_value = {"config": {}}

    result = CliRunner().invoke(configure, ["my-exp", *BASE_ARGS, "-gt", "custom"])

    assert result.exit_code != 0
    assert "Custom type is not supported yet" in result.output
    save_experiment_config.assert_not_called()


# Checks that the command reports a custom executor type as unsupported.
@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
def test_configure_rejects_custom_executor_type(
    is_experiment_exists: MagicMock, read_experiment_data: MagicMock, save_experiment_config: MagicMock
) -> None:
    read_experiment_data.return_value = {"config": {}}

    result = CliRunner().invoke(configure, ["my-exp", *BASE_ARGS, "-et", "custom"])

    assert result.exit_code != 0
    assert "Custom type is not supported yet" in result.output
    save_experiment_config.assert_not_called()


# Checks that the command reports a custom report builder type as unsupported.
@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
def test_configure_rejects_custom_report_builder_type(
    is_experiment_exists: MagicMock, read_experiment_data: MagicMock, save_experiment_config: MagicMock
) -> None:
    read_experiment_data.return_value = {"config": {}}

    result = CliRunner().invoke(configure, ["my-exp", *BASE_ARGS, "-rbt", "custom"])

    assert result.exit_code != 0
    assert "Custom type is not supported yet" in result.output
    save_experiment_config.assert_not_called()


# Checks that a missing config section is tolerated and replaced by an empty dict.
@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
def test_configure_handles_absent_config_section(
    is_experiment_exists: MagicMock, read_experiment_data: MagicMock, save_experiment_config: MagicMock
) -> None:
    read_experiment_data.return_value = {"name": "my-exp", "config": None}

    result = CliRunner().invoke(configure, ["my-exp", *BASE_ARGS])

    assert result.exit_code == 0, f"output={result.output!r} exc={result.exception!r}"
    saved_config: dict[str, Any] = save_experiment_config.call_args[0][1]
    assert saved_config["storage_connection"] == "sqlite:///db.sqlite"
    assert saved_config["sample_sizes"] == [23]


# Checks that a worker count above the CPU limit aborts the whole configuration.
@patch("pysatl_experiment.cli.commands.configure.mp.cpu_count", return_value=1)
@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
def test_configure_rejects_too_many_workers(
    is_experiment_exists: MagicMock,
    read_experiment_data: MagicMock,
    save_experiment_config: MagicMock,
    cpu_count: MagicMock,
) -> None:
    read_experiment_data.return_value = {"config": {}}

    result = CliRunner().invoke(configure, ["my-exp", *BASE_ARGS, "-w", "64"])

    assert result.exit_code != 0
    assert "Cannot set parallel workers to 64" in result.output
    save_experiment_config.assert_not_called()


# Checks that the successful path persists the fully assembled configuration.
@patch("pysatl_experiment.cli.commands.configure.mp.cpu_count", return_value=8)
@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
def test_configure_success_persists_full_config(
    is_experiment_exists: MagicMock,
    read_experiment_data: MagicMock,
    save_experiment_config: MagicMock,
    cpu_count: MagicMock,
) -> None:
    read_experiment_data.return_value = {"config": {}}

    result = CliRunner().invoke(configure, ["my-exp", *BASE_ARGS, "-l", "0.05", "-w", "2"])

    assert result.exit_code == 0, f"output={result.output!r} exc={result.exception!r}"
    saved_config: dict[str, Any] = save_experiment_config.call_args[0][1]
    assert saved_config["experiment_type"] == "power"
    assert saved_config["hypothesis"] == "normal"
    assert saved_config["significance_levels"] == [0.05]
    assert saved_config["parallel_workers"] == 2
    assert "successfully configured" in result.output
