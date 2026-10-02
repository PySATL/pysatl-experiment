"""Report points use structured keys rather than presentation labels."""

from dataclasses import replace

import pytest

from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_series import (
    TimeComplexityReportSeries,
)
from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_statistic import (
    TimeComplexityReportStatistic,
)


def test_statistics_group_and_sort_points_by_complete_series_identity():
    first = TimeComplexityReportSeries("KS", (("location", 1.0),), "normal", 100)
    second = replace(first, criterion_parameters=(("location", 2.0),))
    statistic = TimeComplexityReportStatistic()
    statistic.add_criterion_statistic(first, 20, 0.002)
    statistic.add_criterion_statistic(first, 10, 0.001)
    statistic.add_criterion_statistic(second, 10, 0.003)
    assert statistic.as_dict() == {first: [(10, 0.001), (20, 0.002)], second: [(10, 0.003)]}


def test_duplicate_points_do_not_silently_replace_measurements():
    series = TimeComplexityReportSeries("KS", (), "normal", 100)
    statistic = TimeComplexityReportStatistic()
    statistic.add_criterion_statistic(series, 10, 0.001)
    with pytest.raises(ValueError, match="Duplicate sample size"):
        statistic.add_criterion_statistic(series, 10, 0.002)
    assert statistic.as_dict() == {series: [(10, 0.001)]}
