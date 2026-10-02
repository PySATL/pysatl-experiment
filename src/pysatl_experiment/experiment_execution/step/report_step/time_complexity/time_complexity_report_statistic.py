"""Prepared chart and table points grouped by structured report-series identity."""

from collections.abc import ItemsView
from dataclasses import dataclass, field
from typing import TypeAlias

from .time_complexity_report_series import TimeComplexityReportSeries


TimeComplexityPoint: TypeAlias = tuple[int, float]
TimeComplexityCriterionStatistic: TypeAlias = list[TimeComplexityPoint]
TimeComplexityReportStatisticData: TypeAlias = dict[TimeComplexityReportSeries, TimeComplexityCriterionStatistic]


@dataclass
class TimeComplexityReportStatistic:
    """Average execution times in seconds, separated by complete series identity."""

    values: TimeComplexityReportStatisticData = field(default_factory=dict)

    def add_criterion_statistic(
        self,
        series: TimeComplexityReportSeries,
        sample_size: int,
        statistic: float,
    ) -> None:
        """Add a point, rejecting duplicate sizes instead of replacing measurements."""
        points = self.values.setdefault(series, [])
        if any(size == sample_size for size, _ in points):
            raise ValueError(f"Duplicate sample size {sample_size} for report series {series}")
        points.append((sample_size, statistic))
        points.sort(key=lambda point: point[0])

    def items(self) -> ItemsView[TimeComplexityReportSeries, TimeComplexityCriterionStatistic]:
        """Return series in a stable order for chart construction."""
        return self.as_dict().items()

    def as_dict(self) -> TimeComplexityReportStatisticData:
        """Return sorted structured series and their sample-size points."""
        return dict(sorted(self.values.items()))
