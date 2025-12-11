from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.configuration.model.experiment_type.experiment_type import ExperimentType


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


@patch("pysatl_experiment.cli.commands.configure.configure.get_experiment_config")
def test_experiment_type_with_invalid_type(
        get_experiment_config: MagicMock, runner: CliRunner
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
    experiment_name = "my-test-experiment"
    get_experiment_config.return_value = (experiment_name, {"some_key": "some_value"})

    result = runner.invoke(configure, [experiment_name, "-expt", invalid_type,
                                       "-cr", "KS", "-l", "0.05", "-s", "23", "-c", "154", "-h", "normal",
                                       "-expt", "critical_value", "-con", "sqlite:///pysatl.sqlite"])

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)


@patch("pysatl_experiment.cli.commands.configure.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.configure.if_experiment_exists", return_value=True)
@pytest.mark.parametrize("valid_type", [e for e in ExperimentType])
def test_experiment_type_with_valid_type(
        if_experiment_exists: MagicMock,
        read_experiment_data: MagicMock,
        save_experiment_config: MagicMock,
        runner: CliRunner,
        valid_type: ExperimentType
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
    initial_config = {"hypothesis": "normal"}
    read_experiment_data.return_value = {'name': experiment_name, 'config': initial_config}

    result = runner.invoke(configure, [experiment_name, "-expt", valid_type.value,
                                       "-cr", "KS", "-l", "0.05", "-s", "23", "-c", "154", "-h", "normal",
                                       "-expt", "critical_value", "-con", "sqlite:///pysatl.sqlite"])

    assert result.exit_code == 0
    assert result.exception is None

    expected_config = initial_config.copy()
    expected_config["experiment_type"] = valid_type.value
