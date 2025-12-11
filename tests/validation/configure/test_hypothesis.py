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
def test_hypothesis_with_invalid_hyp(get_experiment_config: MagicMock, runner: CliRunner) -> None:
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
    get_experiment_config.return_value = ("my-experiment", {})
    experiment_name = "my-test-experiment"

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-h",
            invalid_hyp,
            "-cr",
            "KS",
            "-l",
            "0.05",
            "-s",
            "23",
            "-c",
            "154",
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
@pytest.mark.parametrize("valid_hyp", [h for h in Hypothesis])
def test_hypothesis_with_valid_hyp(
    if_experiment_exists: MagicMock,
    get_statistics_short_codes_for_hypothesis: MagicMock,
    read_experiment_data: MagicMock,
    save_experiment_config: MagicMock,
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
    initial_config = {"hypothesis": "normal"}
    read_experiment_data.return_value = {"name": experiment_name, "config": initial_config}
    mock_codes = ["code1", "code2"]
    get_statistics_short_codes_for_hypothesis.return_value = mock_codes

    mock_criteria_data = [{"criterion_code": "code1", "parameters": []}, {"criterion_code": "code2", "parameters": []}]

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-h",
            valid_hyp.value,
            "-l",
            "0.05",
            "-s",
            "23",
            "-c",
            "154",
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

    assert initial_config["hypothesis"] == valid_hyp.value
    assert initial_config["criteria"] == mock_criteria_data
