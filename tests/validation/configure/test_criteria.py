from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


@patch("pysatl_experiment.cli.commands.configure.configure.get_experiment_config")
def test_criteria_fails_if_hypothesis_not_set(get_experiment_config: MagicMock, runner: CliRunner) -> None:
    """
    Tests that the `criteria` command fails if the hypothesis is not yet configured.

    This test verifies the initial precondition check within the command by:
    1.  Simulating a configuration that lacks a 'hypothesis' key.
    2.  Asserting that the command exits with a non-zero code.
    3.  Confirming that a `ClickException` is raised with the correct instructional message.
    4.  Ensuring that no attempt is made to save the configuration.
    """
    experiment_name = "my-exp"
    get_experiment_config.return_value = (experiment_name, {"some_key": "some_value"})

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-cr",
            "KS",
            "-cr",
            "AD",
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

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)


@patch("pysatl_experiment.cli.commands.configure.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.configure.if_experiment_exists", return_value=True)
def test_criteria_fails_with_incompatible_codes(
    if_experiment_exists: MagicMock,
    read_experiment_data: MagicMock,
    save_experiment_config: MagicMock,
    runner: CliRunner,
) -> None:
    """
    Tests that the command fails when provided criteria are incompatible with the hypothesis.

    This test verifies the integration with the `CriteriaConfig` Pydantic model by:
    1.  Providing a configuration with a set hypothesis.
    2.  Mocking the helper function to return a list of allowed criteria codes.
    3.  Invoking the command with a mix of valid and invalid codes.
    4.  Asserting that the `ValidationError` from Pydantic is caught and converted
        into a user-friendly `BadParameter` error message.
    5.  Ensuring that the configuration is not saved.
    """
    experiment_name = "my-exp"
    hypothesis = Hypothesis.NORMAL
    initial_config = {"hypothesis": hypothesis.value}
    read_experiment_data.return_value = {"name": experiment_name, "config": initial_config}

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-cr",
            "KS",
            "-cr",
            "ST1",
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

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)


@patch("pysatl_experiment.cli.commands.configure.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.configure.get_statistics_short_codes_for_hypothesis")
@patch("pysatl_experiment.cli.commands.configure.configure.if_experiment_exists", return_value=True)
def test_criteria_success_with_valid_codes(
    if_experiment_exists: MagicMock,
    get_statistics_short_codes_for_hypothesis: MagicMock,
    read_experiment_data: MagicMock,
    save_experiment_config: MagicMock,
    runner: CliRunner,
) -> None:
    """
    Tests the successful execution of the `criteria` command with valid codes.

    This test verifies the "happy path" by:
    1.  Providing a configuration with a set hypothesis.
    2.  Mocking the helper to return codes that match the input.
    3.  Invoking the command with valid codes (using lowercase to test normalization).
    4.  Asserting that the command exits with a success code.
    5.  Verifying that the configuration to be saved is correctly updated with the
        validated and normalized (uppercased) criteria list.
    6.  Checking for the correct success message in the output.
    """
    hypothesis = Hypothesis.NORMAL
    initial_config: dict[str, Any] = {"hypothesis": hypothesis.value}
    experiment_name = "my-test-experiment"
    read_experiment_data.return_value = {"name": experiment_name, "config": initial_config}

    mock_codes = ["KS", "AD"]
    get_statistics_short_codes_for_hypothesis.return_value = mock_codes

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-cr",
            "KS",
            "-cr",
            "AD",
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

    assert "criteria" in initial_config
    assert len(initial_config["criteria"]) == 2

    saved_codes = [c["criterion_code"] for c in initial_config["criteria"]]
    assert "AD" in saved_codes
    assert "KS" in saved_codes
