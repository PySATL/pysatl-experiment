"""Tests for report mode validation."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure import configure
from pysatl_experiment.configuration.models.report_mode import ReportMode


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


def test_report_mode_with_invalid_mode(runner: CliRunner) -> None:
    """Tests that the command rejects an invalid ReportMode value.

    The invalid value is caught by Click during argument parsing, so the
    command never runs and neither the experiment is looked up nor the
    config is saved.
    """
    invalid_mode = "this-is-not-a-valid-mode"
    experiment_name = "my-test-experiment"

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-rp",
            invalid_mode,
            "-cr",
            "KS",
            "-l",
            "0.05",
            "-s",
            "23",
            "-c",
            "154",
            "-h",
            "normal",
            "-expt",
            "critical_value",
            "-con",
            "sqlite:///pysatl.sqlite",
            "-rm",
            "reuse",
        ],
    )

    assert result.exit_code == 2
    assert isinstance(result.exception, SystemExit)
    assert "Invalid value" in result.output
    assert invalid_mode in result.output


@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
@pytest.mark.parametrize("valid_mode", [e for e in ReportMode])
def test_report_mode_with_valid_mode(
    is_experiment_exists: MagicMock,
    read_experiment_data: MagicMock,
    save_experiment_config: MagicMock,
    runner: CliRunner,
    valid_mode: ReportMode,
) -> None:
    """Tests the `report_mode` command logic in isolation with valid arguments.

    This test verifies that when the command is invoked with any valid `ReportMode`
    enum value, it behaves correctly by:
    1.  Exiting with a zero status code to indicate success.
    2.  Calling the configuration saving function exactly once.
    3.  Updating the configuration dictionary with the correct key and value.
    """
    experiment_name = "my-test-experiment"
    initial_config = {"hypothesis": "normal"}
    read_experiment_data.return_value = {"name": experiment_name, "config": initial_config}

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-rp",
            valid_mode.value,
            "-cr",
            "KS",
            "-l",
            "0.05",
            "-s",
            "23",
            "-c",
            "154",
            "-h",
            "normal",
            "-expt",
            "critical_value",
            "-con",
            "sqlite:///pysatl.sqlite",
            "-rm",
            "reuse",
        ],
    )

    assert result.exit_code == 0
    assert result.exception is None

    assert initial_config["report_mode"] == valid_mode.value

    is_experiment_exists.assert_called_once_with(experiment_name)
    read_experiment_data.assert_called_once_with(experiment_name)
    save_experiment_config.assert_called_once_with(experiment_name, initial_config)
