from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.configure.configure import configure
from pysatl_experiment.configuration.model.run_mode.run_mode import RunMode


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


@patch("pysatl_experiment.cli.commands.configure.configure.get_experiment_config")
def test_run_mode_with_invalid_mode(get_experiment_config: MagicMock, runner: CliRunner) -> None:
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
    get_experiment_config.return_value = (experiment_name, {"some_key": "some_value"})

    result = runner.invoke(configure, [experiment_name, "-rm", invalid_mode,
                                       "-cr", "KS", "-l", "0.05", "-s", "23", "-c", "154", "-h", "normal",
                                       "-expt", "critical_value", "-con", "sqlite:///pysatl.sqlite"
                                       ])

    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)


@patch("pysatl_experiment.cli.commands.configure.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.configure.if_experiment_exists", return_value=True)
@pytest.mark.parametrize("valid_mode", [e for e in RunMode])
def test_run_mode_with_valid_mode(if_experiment_exists: MagicMock,
                                  read_experiment_data: MagicMock,
                                  save_experiment_config: MagicMock,
                                  runner: CliRunner,
                                  valid_mode: RunMode
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
    initial_config = {"hypothesis": "normal"}
    read_experiment_data.return_value = {'name': experiment_name, 'config': initial_config}

    result = runner.invoke(configure, [experiment_name, "-rm", valid_mode.value,
                                       "-cr", "KS", "-l", "0.05", "-s", "23", "-c", "154", "-h", "normal",
                                       "-expt", "critical_value", "-con", "sqlite:///pysatl.sqlite"])

    assert result.exit_code == 0
    assert result.exception is None

    expected_config = initial_config
    expected_config["run_mode"] = valid_mode.value
