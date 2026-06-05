"""Time complexity report building step implementation."""

from pathlib import Path

import numpy as np
from line_profiler import profile
from typing_extensions import override

from pysatl_experiment.configuration.criteria_config.criteria_config import CriterionConfig
from pysatl_experiment.configuration.model.report_mode.report_mode import ReportMode
from pysatl_experiment.experiment.model.experiment_step.experiment_step import IExperimentStep
from pysatl_experiment.persistence.model.time_complexity.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityQuery,
)
from pysatl_experiment.report.time_complexity.time_complexity import TimeComplexityReportBuilder


class TimeComplexityReportBuildingStep(IExperimentStep):
    """Standard time complexity experiment report building step."""

    def __init__(
        self,
        report_name: str,
        criteria_config: list[CriterionConfig],
        sample_sizes: list[int],
        monte_carlo_count: int,
        result_storage: ITimeComplexityStorage,
        results_path: Path,
        with_chart: ReportMode,
    ) -> None:
        """
        Initialize time complexity report building step.

        Parameters
        ----------
        criteria_config : list[CriterionConfig]
            Statistical criteria configurations.
        sample_sizes : list[int]
            Sample sizes used in experiments.
        monte_carlo_count : int
            Number of Monte Carlo iterations.
        result_storage : ITimeComplexityStorage
            Storage with execution time measurements.
        results_path : Path
            Output directory for generated reports.
        with_chart : ReportMode
            Report visualization mode.
        """
        self.report_name = report_name
        self.criteria_config = criteria_config
        self.sizes = sorted(sample_sizes)
        self.monte_carlo_count = monte_carlo_count
        self.result_storage = result_storage
        self.results_path = results_path
        self.with_chart = with_chart

    @profile
    @override
    def run(self) -> None:
        """Collect timing statistics and build report."""
        times_data = self._collect_statistics()

        report_builder = TimeComplexityReportBuilder(
            report_name=self.report_name,
            criteria_config=self.criteria_config,
            sample_sizes=self.sizes,
            times=times_data,
            results_path=self.results_path,
            with_chart=self.with_chart,
        )
        report_builder.build()

    def _collect_statistics(self) -> dict[str, list[tuple[int, float]]]:
        """
        Collect average execution times for each criterion.

        Returns
        -------
        dict[str, list[tuple[int, float]]]
            Mapping of criterion codes to average execution times.
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

    @staticmethod
    def _get_times_from_storage(
        storage: ITimeComplexityStorage,
        criterion_config: CriterionConfig,
        sample_size: int,
        monte_carlo_count: int,
    ) -> list[float]:
        """
        Load execution time measurements from storage.

        Parameters
        ----------
        storage : ITimeComplexityStorage
            Time complexity storage.
        criterion_config : CriterionConfig
            Criterion configuration.
        sample_size : int
            Sample size.
        monte_carlo_count : int
            Number of Monte Carlo iterations.

        Returns
        -------
        list[float]
            Execution times.

        Raises
        ------
        ValueError
            If timing results are not found.
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
