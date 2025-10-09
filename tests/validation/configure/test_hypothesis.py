from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure.hypothesis.hypothesis import hypothesis
from pysatl_experiment.configuration.model.hypothesis.hypothesis import Hypothesis


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


@patch("pysatl_experiment.cli.commands.configure.hypothesis.hypothesis.get_experiment_name_and_config")
@patch("pysatl_experiment.cli.commands.configure.hypothesis.hypothesis.save_experiment_config")
def test_hypothesis_with_invalid_hyp(
    mock_save_config: MagicMock, mock_get_config: MagicMock, runner: CliRunner
) -> None:
    """
    Tests the `hypothesis` command logic with an invalid hypothesis string.

    This test verifies that when the command is invoked with a string that
    does not correspond to any valid `Hypothesis` enum value, it behaves correctly by:
    1.  Calling the function to get the configuration (as it happens before validation).
    2.  Exiting with a non-zero status code upon validation failure.
    3.  Printing an error message that includes the invalid input and lists
        the valid options.
    4.  Not calling the function to save the configuration, thus preventing
        any side effects.
    """
    invalid_hyp = "this-is-not-a-valid-hypothesis"
    mock_get_config.return_value = ("my-experiment", {})

    result = runner.invoke(hypothesis, [invalid_hyp])

    mock_get_config.assert_called_once()

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)

    output = result.output
    assert f"Type of '{invalid_hyp}' is not valid." in output
    valid_options = [e.value for e in Hypothesis]
    assert f"Possible values are: {valid_options}" in output

    mock_save_config.assert_not_called()


@patch("pysatl_experiment.cli.commands.configure.hypothesis.hypothesis.criteria_from_codes")
@patch("pysatl_experiment.cli.commands.configure.hypothesis.hypothesis.get_statistics_short_codes_for_hypothesis")
@patch("pysatl_experiment.cli.commands.configure.hypothesis.hypothesis.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.hypothesis.hypothesis.get_experiment_name_and_config")
@pytest.mark.parametrize("valid_hyp", [h for h in Hypothesis])
def test_hypothesis_with_valid_hyp(
    mock_get_config: MagicMock,
    mock_save_config: MagicMock,
    mock_get_codes: MagicMock,
    mock_criteria_from_codes: MagicMock,
    runner: CliRunner,
    valid_hyp: Hypothesis,
) -> None:
    """
    Tests the `hypothesis` command logic with a valid hypothesis.

    This test verifies that when the command is invoked with a valid `Hypothesis`
    value, it correctly performs all its intended side effects:
    1.  Fetches the initial experiment configuration.
    2.  Updates the 'hypothesis' key in the configuration.
    3.  Calls helper functions to get the appropriate statistical criteria.
    4.  Updates the 'criteria' key in the configuration with the new data.
    5.  Saves the fully updated configuration.
    6.  Exits with a zero status code and prints a success message.
    """
    experiment_name = "my-test-experiment"
    initial_config = {"some_key": "some_value"}
    mock_get_config.return_value = (experiment_name, initial_config.copy())

    mock_codes = ["code1", "code2"]
    mock_criteria_data = [{"name": "Criteria 1"}, {"name": "Criteria 2"}]
    mock_get_codes.return_value = mock_codes
    mock_criteria_from_codes.return_value = mock_criteria_data

    result = runner.invoke(hypothesis, [valid_hyp.value])

    assert result.exit_code == 0
    assert result.exception is None

    mock_get_config.assert_called_once()
    mock_get_codes.assert_called_once_with(valid_hyp.value)
    mock_criteria_from_codes.assert_called_once_with(mock_codes)

    mock_save_config.assert_called_once()

    saved_config = mock_save_config.call_args[0][2]

    assert saved_config["hypothesis"] == valid_hyp.value
    assert saved_config["criteria"] == mock_criteria_data

    assert f"Hypothesis of the experiment '{experiment_name}' is set to '{valid_hyp.value}'" in result.output
    assert f"all criteria for the hypothesis '{valid_hyp.value}' are set" in result.output
