"""Tests for the available-criteria CLI command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pysatl_experiment.cli.commands.criteria import available_criteria


# Checks that a single distribution lists its criterion codes.
@patch("pysatl_experiment.cli.commands.criteria.get_statistics_short_codes_for_hypothesis")
def test_available_criteria_lists_single_distribution_codes(get_codes: MagicMock) -> None:
    get_codes.return_value = ["KS", "AD"]

    result = CliRunner().invoke(available_criteria, ["-d", "normal"])

    assert result.exit_code == 0
    assert "Available criteria for normal:" in result.output
    assert "code: KS" in result.output
    assert "code: AD" in result.output
    get_codes.assert_called_once_with("normal")


# Checks that omitting the distribution lists every distribution group.
@patch("pysatl_experiment.cli.commands.criteria.get_statistics_short_codes_for_hypothesis")
def test_available_criteria_lists_all_distributions(get_codes: MagicMock) -> None:
    get_codes.return_value = {"normal": ["KS"], "exponential": ["AD"]}

    result = CliRunner().invoke(available_criteria, [])

    assert result.exit_code == 0
    assert "Available criteria for normal:" in result.output
    assert "code: KS" in result.output
    assert "Available criteria for exponential:" in result.output
    assert "code: AD" in result.output
    get_codes.assert_called_once_with(None)


# Checks the empty result branch prints the no-criteria notice.
@patch("pysatl_experiment.cli.commands.criteria.get_statistics_short_codes_for_hypothesis", return_value=[])
def test_available_criteria_reports_no_criteria(get_codes: MagicMock) -> None:
    result = CliRunner().invoke(available_criteria, ["-d", "normal"])

    assert result.exit_code == 0
    assert "No criteria found" in result.output


# Checks that an empty group is flagged while listing all distributions.
@patch("pysatl_experiment.cli.commands.criteria.get_statistics_short_codes_for_hypothesis")
def test_available_criteria_all_distributions_flags_empty_groups(get_codes: MagicMock) -> None:
    get_codes.return_value = {"normal": []}

    result = CliRunner().invoke(available_criteria, [])

    assert result.exit_code == 0
    assert "Available criteria for normal:" in result.output
    assert "No criteria found" in result.output


# Checks that the reserved --description flag is accepted by the command.
@patch("pysatl_experiment.cli.commands.criteria.get_statistics_short_codes_for_hypothesis")
def test_available_criteria_description_flag_is_accepted(get_codes: MagicMock) -> None:
    get_codes.return_value = ["KS"]

    result = CliRunner().invoke(available_criteria, ["-d", "normal", "-y"])

    assert result.exit_code == 0
    assert "code: KS" in result.output


# Checks that an unknown distribution value is rejected by the click Choice option.
def test_available_criteria_rejects_unknown_distribution() -> None:
    result = CliRunner().invoke(available_criteria, ["-d", "not-a-distribution"])

    assert result.exit_code == 2
    assert "Invalid value" in result.output


# Checks that each valid distribution value is forwarded to the helper.
@pytest.mark.parametrize("distribution", ["normal", "exponential", "weibull"])
@patch("pysatl_experiment.cli.commands.criteria.get_statistics_short_codes_for_hypothesis")
def test_available_criteria_forwards_distribution(get_codes: MagicMock, distribution: str) -> None:
    get_codes.return_value = ["KS"]

    result = CliRunner().invoke(available_criteria, ["-d", distribution])

    assert result.exit_code == 0
    get_codes.assert_called_once_with(distribution)
