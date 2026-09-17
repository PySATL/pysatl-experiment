"""Tests for hypothesis validation."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from pysatl_criterion import DistributionType

from pysatl_experiment.cli.commands.configure import configure


@pytest.fixture
def runner() -> CliRunner:
    """Fixture to create a CliRunner instance."""
    return CliRunner()


def test_hypothesis_with_invalid_hyp(runner: CliRunner) -> None:
    """Tests that the command rejects an invalid hypothesis value.

    The invalid value is caught by Click during argument parsing, so the
    command never runs and the config is not saved.
    """
    invalid_hyp = "this-is-not-a-valid-hypothesis"
    experiment_name = "my-test-experiment"

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-h", invalid_hyp,
            "-cr", "KS",
            "-l", "0.05",
            "-s", "23",
            "-c", "154",
            "-expt", "critical_value",
            "-con", "sqlite:///pysatl.sqlite",
            "-rm", "reuse",
        ],
    )

    assert result.exit_code == 2
    assert isinstance(result.exception, SystemExit)
    assert "Invalid value" in result.output
    assert invalid_hyp in result.output


@patch("pysatl_experiment.cli.commands.configure.save_experiment_config")
@patch("pysatl_experiment.cli.commands.configure.read_experiment_data")
@patch("pysatl_experiment.cli.commands.configure.get_statistics_short_codes_for_hypothesis")
@patch("pysatl_experiment.cli.commands.configure.criteria_from_codes")
@patch("pysatl_experiment.cli.commands.configure.is_experiment_exists", return_value=True)
@pytest.mark.parametrize("valid_hyp", [h for h in DistributionType])
def test_hypothesis_with_valid_hyp(
    is_experiment_exists: MagicMock,
    criteria_from_codes: MagicMock,
    get_statistics_short_codes_for_hypothesis: MagicMock,
    read_experiment_data: MagicMock,
    save_experiment_config: MagicMock,
    runner: CliRunner,
    valid_hyp: DistributionType,
) -> None:
    """Tests the `hypothesis` command logic with a valid hypothesis.

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
    get_statistics_short_codes_for_hypothesis.return_value = ["KS", "AD"]
    criteria_from_codes.return_value = [
        {"criterion_code": "KS"},
        {"criterion_code": "AD"},
    ]

    result = runner.invoke(
        configure,
        [
            experiment_name,
            "-h", valid_hyp.value,
            "-l", "0.05",
            "-s", "23",
            "-c", "154",
            "-expt", "critical_value",
            "-con", "sqlite:///pysatl.sqlite",
            "-rm", "reuse",
        ],
    )

    assert result.exit_code == 0, f"output={result.output!r} exc={result.exception!r}"
    assert result.exception is None

    assert initial_config["hypothesis"] == valid_hyp.value
    assert initial_config["criteria"] == [{"criterion_code": "KS"}, {"criterion_code": "AD"}]

    is_experiment_exists.assert_called_once_with(experiment_name)
    read_experiment_data.assert_called_once_with(experiment_name)
    get_statistics_short_codes_for_hypothesis.assert_called_once_with(valid_hyp.value)
    save_experiment_config.assert_called_once_with(experiment_name, initial_config)
