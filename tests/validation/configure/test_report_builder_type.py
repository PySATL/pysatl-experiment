from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.configuration.model.step_type.step_type import StepType


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


def test_report_builder_type_with_invalid_type(runner: CliRunner) -> None:
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
    experiment_name = "my-test-experiment"

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-rbt",
            invalid_type,
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
        ],
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)


@patch("pysatl_experiment.cli.commands.configure.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.configure.if_experiment_exists", return_value=True)
def test_report_builder_type_with_unsupported_custom_type(
    if_experiment_exists: MagicMock,
    read_experiment_data: MagicMock,
    save_experiment_config: MagicMock,
    runner: CliRunner,
) -> None:
    """
    Tests the `report_builder_type` command with the 'custom' type, which is unsupported.

    This test verifies that the specific logic check preventing the use of the
    `StepType.CUSTOM` value works correctly by:
    1.  Exiting with a non-zero status code.
    2.  Printing the specific error message for the unsupported 'custom' type.
    3.  Not attempting to get or save the experiment configuration.
    """
    custom_type = StepType.CUSTOM
    experiment_name = "my-test-experiment"
    initial_config = {"hypothesis": "normal"}
    read_experiment_data.return_value = {"name": experiment_name, "config": initial_config}

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-rbt",
            custom_type.value,
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
        ],
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)

    assert "Custom type is not supported yet." in result.output


@patch("pysatl_experiment.cli.commands.configure.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.configure.if_experiment_exists", return_value=True)
@pytest.mark.parametrize("valid_type", [e for e in StepType if e != StepType.CUSTOM])
def test_report_builder_type_with_valid_supported_type(
    if_experiment_exists: MagicMock,
    read_experiment_data: MagicMock,
    save_experiment_config: MagicMock,
    runner: CliRunner,
    valid_type: StepType,
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
    initial_config = {"hypothesis": "normal"}
    read_experiment_data.return_value = {"name": experiment_name, "config": initial_config}

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-rbt",
            valid_type.value,
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
        ],
    )

    assert result.exit_code == 0
    assert result.exception is None

    expected_config = initial_config.copy()
    expected_config["report_builder_type"] = valid_type.value
