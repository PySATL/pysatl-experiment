"""Tests for the time complexity report statistics container."""

from __future__ import annotations

import pytest

from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_statistic import (
    TimeComplexityReportStatistic,
)


# Checks that a new container starts with an empty values mapping.
def test_default_values_are_empty() -> None:
    assert TimeComplexityReportStatistic().values == {}


# Checks that separately created containers do not share their values mapping.
def test_instances_do_not_share_values() -> None:
    first = TimeComplexityReportStatistic()
    second = TimeComplexityReportStatistic()

    first.add_criterion_statistic("KS_", 10, 0.5)

    assert second.as_dict() == {}


# Checks that a statistic is appended for a previously unseen criterion.
def test_add_creates_criterion_entry() -> None:
    statistic = TimeComplexityReportStatistic()

    statistic.add_criterion_statistic("KS_", 10, 0.5)

    assert statistic.as_dict() == {"KS_": [(10, 0.5)]}


# Checks that several sample sizes of one criterion are kept ordered by size.
def test_add_keeps_points_sorted_by_sample_size() -> None:
    statistic = TimeComplexityReportStatistic()

    for size, value in ((50, 0.5), (10, 0.1), (30, 0.3)):
        statistic.add_criterion_statistic("KS_", size, value)

    assert statistic.as_dict() == {"KS_": [(10, 0.1), (30, 0.3), (50, 0.5)]}


# Checks that re-adding the same sample size replaces the stored value in place.
@pytest.mark.parametrize("replacement", [0.9, 0.0, -1.0])
def test_add_replaces_existing_sample_size(replacement: float) -> None:
    statistic = TimeComplexityReportStatistic()
    statistic.add_criterion_statistic("KS_", 10, 0.1)
    statistic.add_criterion_statistic("KS_", 20, 0.2)

    statistic.add_criterion_statistic("KS_", 10, replacement)

    assert statistic.as_dict() == {"KS_": [(10, replacement), (20, 0.2)]}


# Checks that statistics of different criteria are stored in separate groups.
def test_add_groups_by_criterion_code() -> None:
    statistic = TimeComplexityReportStatistic()

    statistic.add_criterion_statistic("KS_", 10, 0.1)
    statistic.add_criterion_statistic("AD_", 10, 0.9)

    assert statistic.as_dict() == {"KS_": [(10, 0.1)], "AD_": [(10, 0.9)]}


# Checks that the values mapping is returned as-is from as_dict.
def test_as_dict_returns_stored_mapping() -> None:
    statistic = TimeComplexityReportStatistic({"KS_": [(10, 0.1)]})

    assert statistic.as_dict() is statistic.values


# Checks that items exposes the criterion entries of the container.
def test_items_returns_criterion_entries() -> None:
    statistic = TimeComplexityReportStatistic()
    statistic.add_criterion_statistic("KS_", 10, 0.1)
    statistic.add_criterion_statistic("AD_", 20, 0.2)

    assert dict(statistic.items()) == {"KS_": [(10, 0.1)], "AD_": [(20, 0.2)]}


# Checks that an empty container yields no items.
def test_items_is_empty_for_new_container() -> None:
    assert dict(TimeComplexityReportStatistic().items()) == {}
