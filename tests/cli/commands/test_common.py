"""Tests for CLI common functionality."""

import pytest
from pysatl_criterion import DistributionType

from pysatl_experiment.cli.commands.common.common import get_statistics_short_codes_for_hypothesis


def test_get_statistics_short_codes_for_single_hypothesis():
    """Should return list[str] for a single hypothesis."""
    hypothesis = DistributionType.NORMAL.value

    result = get_statistics_short_codes_for_hypothesis(hypothesis)

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(code, str) for code in result)


def test_get_statistics_short_codes_for_none():
    """Should return mapping for all hypotheses."""
    result = get_statistics_short_codes_for_hypothesis(None)

    assert isinstance(result, dict)

    expected_keys = {member.value for member in DistributionType}

    assert set(result.keys()) == expected_keys

    for value in result.values():
        assert isinstance(value, list)
        assert all(isinstance(code, str) for code in value)


def test_get_statistics_short_codes_for_list_input():
    """Current implementation ignores provided list and returns all distributions."""
    result = get_statistics_short_codes_for_hypothesis([DistributionType.NORMAL.value])

    expected_keys = {member.value for member in DistributionType}

    assert isinstance(result, dict)
    assert set(result.keys()) == expected_keys


def test_invalid_hypothesis_raises_value_error():
    """Unknown hypothesis should raise ValueError."""
    with pytest.raises(ValueError):
        get_statistics_short_codes_for_hypothesis("invalid_distribution")


def test_returned_codes_do_not_contain_suffix():
    """Codes should be truncated by split('_')[0]."""
    result = get_statistics_short_codes_for_hypothesis(DistributionType.NORMAL.value)

    for code in result:
        assert "_" not in code
