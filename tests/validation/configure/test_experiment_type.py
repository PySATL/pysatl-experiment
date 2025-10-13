from unittest.mock import ANY, MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure.experiment_type.experiment_type import experiment_type
from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


@patch("pysatl_experiment.cli.commands.configure.experiment_type.experiment_type.get_experiment_name_and_config")
@patch("pysatl_experiment.cli.commands.configure.experiment_type.experiment_type.save_experiment_config")
def test_experiment_type_with_invalid_type(
    mock_save_config: MagicMock, mock_get_config: MagicMock, runner: CliRunner
) -> None:
    """
    Tests the `experiment_type` command with an invalid type string.

    This test verifies that when the command is invoked with a string that
    does not correspond to any valid `ExperimentType` enum value, it behaves
    correctly by:
    1.  Exiting with a non-zero status code.
    2.  Printing an error message that includes the invalid input and lists
        the valid options.
    3.  Not calling the function to save the configuration.
    """
    invalid_type = "this-is-not-a-valid-type"
    mock_get_config.return_value = ("my-experiment", {})

    result = runner.invoke(experiment_type, [invalid_type])

    mock_get_config.assert_called_once()

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)

    output = result.output
    assert f"Type of '{invalid_type}' is not valid." in output
    valid_options = [e.value for e in ExperimentType]
    assert f"Possible values are: {valid_options}" in output

    mock_save_config.assert_not_called()


@patch("pysatl_experiment.cli.commands.configure.experiment_type.experiment_type.get_experiment_name_and_config")
@patch("pysatl_experiment.cli.commands.configure.experiment_type.experiment_type.save_experiment_config")
@pytest.mark.parametrize("valid_type", [e for e in ExperimentType])
def test_experiment_type_with_valid_type(
    mock_save_config: MagicMock, mock_get_config: MagicMock, runner: CliRunner, valid_type: ExperimentType
) -> None:
    """
    Tests the `experiment_type` command logic with all valid arguments.

    This test verifies that when the command is invoked with any valid
    `ExperimentType` enum value, it behaves correctly by:
    1.  Exiting with a zero status code for success.
    2.  Calling the functions to get and save the configuration exactly once.
    3.  Updating the configuration dictionary with the correct key and value.
    4.  Printing a confirmation message to the user.
    """
    experiment_name = "my-test-experiment"
    initial_config = {"some_key": "some_value"}
    mock_get_config.return_value = (experiment_name, initial_config.copy())

    result = runner.invoke(experiment_type, [valid_type.value])

    assert result.exit_code == 0
    assert result.exception is None

    mock_get_config.assert_called_once()

    expected_config = initial_config.copy()
    expected_config["experiment_type"] = valid_type.value
    mock_save_config.assert_called_once_with(ANY, experiment_name, expected_config)

    expected_output = f"Type of the experiment '{experiment_name}' is set to '{valid_type.value}'.\n"
    assert result.output == expected_output
