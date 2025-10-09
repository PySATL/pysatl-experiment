from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure.criteria.criteria import criteria
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


@patch("pysatl_experiment.cli.commands.configure.criteria.criteria.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.criteria.criteria.get_experiment_name_and_config")
def test_criteria_fails_if_hypothesis_not_set(
    mock_get_config: MagicMock, mock_save_config: MagicMock, runner: CliRunner
) -> None:
    """
    Tests that the `criteria` command fails if the hypothesis is not yet configured.

    This test verifies the initial precondition check within the command by:
    1.  Simulating a configuration that lacks a 'hypothesis' key.
    2.  Asserting that the command exits with a non-zero code.
    3.  Confirming that a `ClickException` is raised with the correct instructional message.
    4.  Ensuring that no attempt is made to save the configuration.
    """
    experiment_name = "my-exp"
    mock_get_config.return_value = (experiment_name, {})

    result = runner.invoke(criteria, ["KS", "AD"])

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)

    assert "Hypothesis is not configured" in result.output
    assert f"experiment configure {experiment_name} hypothesis <hypothesis>" in result.output
    mock_save_config.assert_not_called()


@patch("pysatl_experiment.validation.cli.schemas.criteria.get_statistics_short_codes_for_hypothesis")
@patch("pysatl_experiment.cli.commands.configure.criteria.criteria.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.criteria.criteria.get_experiment_name_and_config")
def test_criteria_fails_with_incompatible_codes(
    mock_get_config: MagicMock, mock_save_config: MagicMock, mock_get_valid_codes: MagicMock, runner: CliRunner
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
    hypothesis = Hypothesis.NORMAL
    mock_get_config.return_value = ("my-exp", {"hypothesis": hypothesis.value})
    mock_get_valid_codes.return_value = ["KS", "AD"]

    result = runner.invoke(criteria, ["KS", "CVM"])

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)

    assert f"Criteria 'CVM' are incompatible with hypothesis '{hypothesis.value}'" in result.output
    assert "Valid codes: KS, AD" in result.output

    mock_save_config.assert_not_called()


@patch("pysatl_experiment.validation.cli.schemas.criteria.get_statistics_short_codes_for_hypothesis")
@patch("pysatl_experiment.cli.commands.configure.criteria.criteria.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.criteria.criteria.get_experiment_name_and_config")
def test_criteria_success_with_valid_codes(
    mock_get_config: MagicMock, mock_save_config: MagicMock, mock_get_valid_codes: MagicMock, runner: CliRunner
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
    experiment_name = "my-exp"
    hypothesis = Hypothesis.NORMAL
    initial_config = {"hypothesis": hypothesis.value}
    mock_get_config.return_value = (experiment_name, initial_config.copy())

    valid_codes_for_hypothesis = ["KS", "AD", "SW"]
    mock_get_valid_codes.return_value = valid_codes_for_hypothesis

    input_codes = ["ad", "ks"]
    result = runner.invoke(criteria, input_codes)

    assert result.exit_code == 0
    assert result.exception is None

    mock_get_valid_codes.assert_called_once_with(hypothesis.value)

    mock_save_config.assert_called_once()

    saved_config = mock_save_config.call_args[0][2]

    assert "criteria" in saved_config
    assert len(saved_config["criteria"]) == 2

    saved_codes = [c["criterion_code"] for c in saved_config["criteria"]]
    assert "AD" in saved_codes
    assert "KS" in saved_codes

    assert f"Criteria for experiment '{experiment_name}' successfully set: ['AD', 'KS']" in result.output
