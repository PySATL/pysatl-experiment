from unittest.mock import ANY, MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure.run_mode.run_mode import run_mode
from pysatl_experiment.configuration.model.run_mode.run_mode import RunMode


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


@patch("pysatl_experiment.cli.commands.configure.run_mode.run_mode.get_experiment_name_and_config")
@patch("pysatl_experiment.cli.commands.configure.run_mode.run_mode.save_experiment_config")
def test_run_mode_with_invalid_mode(mock_save_config: MagicMock, mock_get_config: MagicMock, runner: CliRunner) -> None:
    """
    Tests the `run_mode` command logic in isolation with an invalid argument.

    This test verifies that when the `run_mode` command is invoked with a string
    that does not correspond to any valid `RunMode` enum value, it behaves
    correctly by:
    1.  Exiting with a non-zero status code to indicate failure.
    2.  Printing a user-friendly error message that includes the invalid input.
    3.  Suggesting the list of valid options to the user.
    4.  Not calling the function to save the configuration, thus preventing
        any side effects.
    """
    invalid_mode = "this-is-not-a-valid-mode"
    experiment_name = "my-test-experiment"
    mock_get_config.return_value = (experiment_name, {"some_key": "some_value"})

    result = runner.invoke(run_mode, [invalid_mode])

    mock_get_config.assert_called_once()

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)

    output = result.output
    expected_error_fragment = f"Type of '{invalid_mode}' is not valid."
    assert expected_error_fragment in output

    valid_options = [e.value for e in RunMode]
    assert f"Possible values are: {valid_options}" in output

    mock_save_config.assert_not_called()


@patch("pysatl_experiment.cli.commands.configure.run_mode.run_mode.get_experiment_name_and_config")
@patch("pysatl_experiment.cli.commands.configure.run_mode.run_mode.save_experiment_config")
@pytest.mark.parametrize("valid_mode", [e for e in RunMode])
def test_run_mode_with_valid_mode(
    mock_save_config: MagicMock, mock_get_config: MagicMock, runner: CliRunner, valid_mode: RunMode
) -> None:
    """
    Tests the `run_mode` command logic in isolation with valid arguments.

    This test verifies that when the command is invoked with any valid `RunMode`
    enum value, it behaves correctly by:
    1.  Exiting with a zero status code to indicate success.
    2.  Calling the configuration saving function exactly once.
    3.  Updating the configuration dictionary with the correct key and value.
    4.  Printing a confirmation message to the user.
    """
    experiment_name = "my-test-experiment"
    initial_config = {"some_key": "some_value"}
    mock_get_config.return_value = (experiment_name, initial_config.copy())

    result = runner.invoke(run_mode, [valid_mode.value])

    mock_get_config.assert_called_once()

    assert result.exit_code == 0
    assert result.exception is None

    expected_config = initial_config.copy()
    expected_config["run_mode"] = valid_mode.value
    mock_save_config.assert_called_once_with(ANY, experiment_name, expected_config)

    expected_output = f"Run mode of the experiment '{experiment_name}' is set to '{valid_mode.value}'.\n"
    assert result.output == expected_output
