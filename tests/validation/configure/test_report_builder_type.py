from unittest.mock import ANY, MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure.report_builder_type.report_builder_type import report_builder_type
from pysatl_experiment.configuration.model.step_type.step_type import StepType


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


@patch(
    "pysatl_experiment.cli.commands.configure.report_builder_type.report_builder_type.get_experiment_name_and_config"
)
@patch("pysatl_experiment.cli.commands.configure.report_builder_type.report_builder_type.save_experiment_config")
def test_report_builder_type_with_invalid_type(
    mock_save_config: MagicMock, mock_get_config: MagicMock, runner: CliRunner
) -> None:
    """
    Tests the `report_builder_type` command with a completely invalid type string.

    This test verifies that when the command is invoked with a string
    that does not correspond to any valid `StepType` enum value, it behaves
    correctly by:
    1.  Exiting with a non-zero status code.
    2.  Printing an error message that includes the invalid input and lists
        the valid options.
    3.  Not attempting to get or save the experiment configuration, as the
        error occurs during initial validation.
    """
    invalid_type = "this-is-not-a-valid-type"

    result = runner.invoke(report_builder_type, [invalid_type])

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)

    output = result.output
    assert f"Type of '{invalid_type}' is not valid." in output
    valid_options = [e.value for e in StepType]
    assert f"Possible values are: {valid_options}" in output

    mock_get_config.assert_not_called()
    mock_save_config.assert_not_called()


@patch(
    "pysatl_experiment.cli.commands.configure.report_builder_type.report_builder_type.get_experiment_name_and_config"
)
@patch("pysatl_experiment.cli.commands.configure.report_builder_type.report_builder_type.save_experiment_config")
def test_report_builder_type_with_unsupported_custom_type(
    mock_save_config: MagicMock, mock_get_config: MagicMock, runner: CliRunner
) -> None:
    """
    Tests the `report_builder_type` command with the 'custom' type, which is unsupported.

    This test verifies that the specific logic check preventing the use of the
    `StepType.CUSTOM` value works correctly by:
    1.  Exiting with a non-zero status code.
    2.  Printing the specific error message for the unsupported 'custom' type.
    3.  Not attempting to get or save the experiment configuration.
    """
    custom_type = StepType.CUSTOM.value

    result = runner.invoke(report_builder_type, [custom_type])

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)

    assert "Custom type is not supported yet." in result.output

    mock_get_config.assert_not_called()
    mock_save_config.assert_not_called()


@patch(
    "pysatl_experiment.cli.commands.configure.report_builder_type.report_builder_type.get_experiment_name_and_config"
)
@patch("pysatl_experiment.cli.commands.configure.report_builder_type.report_builder_type.save_experiment_config")
@pytest.mark.parametrize("valid_type", [e for e in StepType if e != StepType.CUSTOM])
def test_report_builder_type_with_valid_supported_type(
    mock_save_config: MagicMock, mock_get_config: MagicMock, runner: CliRunner, valid_type: StepType
) -> None:
    """
    Tests the `report_builder_type` command logic with all valid and supported arguments.

    This test verifies that when the command is invoked with any supported `StepType`
    enum value, it behaves correctly by:
    1.  Exiting with a zero status code for success.
    2.  Calling the functions to get and save the configuration exactly once.
    3.  Updating the configuration dictionary with the correct key and value.
    4.  Printing a confirmation message to the user.
    """
    experiment_name = "my-test-experiment"
    initial_config = {"some_key": "some_value"}
    mock_get_config.return_value = (experiment_name, initial_config.copy())

    result = runner.invoke(report_builder_type, [valid_type.value])

    assert result.exit_code == 0
    assert result.exception is None

    mock_get_config.assert_called_once()

    expected_config = initial_config.copy()
    expected_config["report_builder_type"] = valid_type.value
    mock_save_config.assert_called_once_with(ANY, experiment_name, expected_config)

    expected_output = f"Report builder type of the experiment '{experiment_name}' is set to '{valid_type.value}'.\n"
    assert result.output == expected_output
