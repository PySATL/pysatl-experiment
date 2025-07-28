from pathlib import Path

import numpy as np

from stattest.configuration.criteria_config.criteria_config import CriterionConfig
from stattest.configuration.model.report_mode.report_mode import ReportMode
from stattest.persistence.model.time_complexity.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityQuery,
)
from stattest.report.time_complexity.time_complexity import TimeComplexityReportBuilder


class TimeComplexityReportBuildingStep:
    """
    Standard time complexity experiment report building step.
    """

    def __init__(
        self,
        criteria_config: list[CriterionConfig],
        sample_sizes: list[int],
        monte_carlo_count: int,
        result_storage: ITimeComplexityStorage,
        results_path: Path,
        with_chart: ReportMode,
    ):
        self.criteria_config = criteria_config
        self.sizes = sorted(sample_sizes)
        self.monte_carlo_count = monte_carlo_count
        self.result_storage = result_storage
        self.results_path = results_path
        self.with_chart = with_chart

    def run(self) -> None:
        """
        Run standard time complexity report building step.
        """

        times_data = self._collect_statistics()

        report_builder = TimeComplexityReportBuilder(
            criteria_config=self.criteria_config,
            sample_sizes=self.sizes,
            times=times_data,
            results_path=self.results_path,
            with_chart=self.with_chart,
        )
        report_builder.build()

    def _collect_statistics(self) -> dict[str, list[tuple[int, float]]]:
        """
        Collect and pre-calculate statistics for each criterion and sample size.

        :returns: dictionary of statistics.
        """
        stats = {}

        for criterion in self.criteria_config:
            criterion_stats = []

            for size in self.sizes:
                times = self._get_times_from_storage(
                    storage=self.result_storage,
                    criterion_config=criterion,
                    sample_size=size,
                    monte_carlo_count=self.monte_carlo_count,
                )

                if times:
                    mean = float(np.mean(times))
                    criterion_stats.append((size, mean))

            stats[criterion.criterion_code] = criterion_stats

        return stats

    def _get_times_from_storage(
        self,
        storage: ITimeComplexityStorage,
        criterion_config: CriterionConfig,
        sample_size: int,
        monte_carlo_count: int,
    ) -> list[float]:
        """
        Get times from time complexity storage.

        :param storage: storage.
        :param criterion_config: criterion configuration.
        :param sample_size: sample size.
        :param monte_carlo_count: monte carlo count.

        :return: times.
        """

        query = TimeComplexityQuery(
            criterion_code=criterion_config.criterion_code,
            criterion_parameters=criterion_config.criterion.parameters,
            sample_size=sample_size,
            monte_carlo_count=monte_carlo_count,
        )

        result = storage.get_data(query)
        if result is None:
            raise ValueError(f"Times for query {query} not found.")

        times = result.results_times

        return times
