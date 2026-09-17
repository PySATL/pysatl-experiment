"""Tests for experiment type validation."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure import configure
from pysatl_experiment.configuration.models.experiment_type import ExperimentType


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


# @patch("pysatl_experiment.cli.commands.configure.get_experiment_config")  get_experiment_config: MagicMock,
def test_experiment_type_with_invalid_type(runner: CliRunner) -> None:
    """Tests the `experiment_type` command with an invalid type string.

    This test verifies that when the command is invoked with a string that
    does not correspond to any valid `ExperimentType` enum value, it behaves
    correctly by:
    1.  Exiting with a non-zero status code.
    2.  Printing an error message that includes the invalid input and lists
        the valid options.
    3.  Not calling the function to save the configuration.
    """
    invalid_type = "this-is-not-a-valid-type"
    experiment_name = "my-test-experiment"
    # get_experiment_config.return_value = (experiment_name, {"some_key": "some_value"})

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-expt", invalid_type,
            "-cr", "KS",
            "-l", "0.05",
            "-s", "23",
            "-c", "154",
            "-h", "normal",
            # "-expt", "critical_value",
            "-con", "sqlite:///pysatl.sqlite",
        ],
    )

    assert result.exit_code == 2
    assert isinstance(result.exception, SystemExit)
    assert "Invalid value" in result.output
    assert invalid_type in result.output


@pytest.mark.parametrize("valid_type", [e for e in ExperimentType])
@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
def test_experiment_type_with_valid_type(
    is_experiment_exists: MagicMock,
    read_experiment_data: MagicMock,
    save_experiment_config: MagicMock,
    runner: CliRunner,
    valid_type: ExperimentType,
) -> None:
    """Tests the `experiment_type` command logic with all valid arguments.

    This test verifies that when the command is invoked with any valid
    `ExperimentType` enum value, it behaves correctly by:
    1.  Exiting with a zero status code for success.
    2.  Calling the functions to get and save the configuration exactly once.
    3.  Updating the configuration dictionary with the correct key and value.
    4.  Printing a confirmation message to the user.

    For most types the command succeeds and stores the type in the config.
    TIME_COMPLEXITY does not support significance levels, so with `-l` the
    command fails before saving the config.
    """
    experiment_name = "my-test-experiment"
    initial_config = {"hypothesis": "normal"}
    read_experiment_data.return_value = {"name": experiment_name, "config": initial_config}

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-expt", valid_type.value,
            "-cr", "KS",
            "-l", "0.05",
            "-s", "23",
            "-c", "154",
            "-h", "normal",
            # "-expt", "critical_value",
            "-con", "sqlite:///pysatl.sqlite",
        ],
    )

    is_experiment_exists.assert_called_once()
    read_experiment_data.assert_called_once()
    assert initial_config["experiment_type"] == valid_type.value

    if valid_type == ExperimentType.TIME_COMPLEXITY:
        assert result.exit_code == 1
        assert "Significance levels are not supported" in result.output
        save_experiment_config.assert_not_called()
    else:
        assert result.exit_code == 0
        assert result.exception is None
        save_experiment_config.assert_called_once_with(experiment_name, initial_config)
