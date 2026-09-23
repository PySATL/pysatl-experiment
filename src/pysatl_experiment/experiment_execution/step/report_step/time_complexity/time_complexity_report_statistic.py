"""Time complexity report statistics."""

from collections.abc import ItemsView
from dataclasses import dataclass, field
from typing import TypeAlias


TimeComplexityPoint: TypeAlias = tuple[int, float]
TimeComplexityCriterionStatistic: TypeAlias = list[TimeComplexityPoint]
TimeComplexityReportStatisticData: TypeAlias = dict[str, TimeComplexityCriterionStatistic]


@dataclass
class TimeComplexityReportStatistic:
    """
    Average execution times grouped by criterion code.

    Parameters
    ----------
    values : TimeComplexityReportStatisticData
        Mapping of criterion code to pairs of sample size and average execution time.
    """

    values: TimeComplexityReportStatisticData = field(default_factory=dict)

    def add_criterion_statistic(
        self,
        criterion_code: str,
        sample_size: int,
        statistic: float,
    ) -> None:
        """
        Store average execution time for a criterion and sample size.

        Parameters
        ----------
        criterion_code : str
            Criterion identifier.
        sample_size : int
            Sample size.
        statistic : float
            Average execution time.
        """
        criterion_statistic = self.values.setdefault(criterion_code, [])

        for idx, (existing_sample_size, _) in enumerate(criterion_statistic):
            if existing_sample_size == sample_size:
                criterion_statistic[idx] = (sample_size, statistic)
                break
        else:
            criterion_statistic.append((sample_size, statistic))
            criterion_statistic.sort(key=lambda point: point[0])

    def items(self) -> ItemsView[str, TimeComplexityCriterionStatistic]:
        """
        Return criterion statistics grouped by criterion code.

        Returns
        -------
        ItemsView[str, TimeComplexityCriterionStatistic]
            Criterion statistics items.
        """
        return self.values.items()

    def as_dict(self) -> TimeComplexityReportStatisticData:
        """
        Return statistics as a plain dictionary.

        Returns
        -------
        TimeComplexityReportStatisticData
            Mapping of criterion code to average execution time points.
        """
        return self.values
