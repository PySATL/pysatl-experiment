"""Time complexity report building step implementation."""

import numpy as np
from line_profiler import profile
from typing_extensions import override

from pysatl_experiment.configuration.models.parameters import NumericParameters
from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_builder import (
    TimeComplexityReportBuilder,
)
from pysatl_experiment.persistence.models.time_complexity import ITimeComplexityStorage, TimeComplexityQuery

from .time_complexity_report_statistic import TimeComplexityReportStatistic
from .time_complexity_report_step_context import TimeComplexityReportStepContext


class TimeComplexityReportBuildingStep(IExperimentStep):
    """Standard time complexity experiment report building step."""

    def __init__(
        self,
        ctx: TimeComplexityReportStepContext,
        result_storage: ITimeComplexityStorage,
    ) -> None:
        """
        Initialize time complexity report building step.

        Parameters
        ----------
        result_storage : ITimeComplexityStorage
            Storage with execution time measurements.
        """
        self.ctx = ctx
        self.result_storage = result_storage
        self.experiment_name = ctx.experiment_name
        self.criteria_config = ctx.criteria_config
        self.sizes = sorted(ctx.sample_sizes)
        self.monte_carlo_count = ctx.monte_carlo_count
        self.results_path = ctx.results_path
        self.with_chart = ctx.report_mode

    @profile
    @override
    def run(self) -> None:
        """Collect timing statistics and build report."""
        statistic = self._collect_statistics()

        TimeComplexityReportBuilder(
            report_name=self.ctx.report_name,
            sample_sizes=self.sizes,
            statistic=statistic,
            results_path=self.results_path,
            report_mode=self.with_chart,
        ).build()

    def _collect_statistics(self) -> TimeComplexityReportStatistic:
        """
        Collect average execution times for each criterion.

        Returns
        -------
        TimeComplexityReportStatistic
            Average execution times grouped by criterion code.
        """
        stats = TimeComplexityReportStatistic()

        # OLD CODE:
        # for data in self.ctx.data_list:
        #    times = self._get_times_from_storage(
        #        experiment_name=self.experiment_name,
        #        criterion_code=data.criterion.code(),
        #        criterion_parameters=data.criterion.hypothesis().parameters(),
        #        sample_size=data.sample_size,
        #        samples_count=self.ctx.samples_count,
        #    )
        #
        #    if times:
        #        mean = float(np.mean(times))
        #        stats.add_criterion_statistic(data.criterion_code, size, mean)

        for criterion in self.criteria_config:
            for size in self.sizes:
                times = self._get_times_from_storage(
                    experiment_name=self.experiment_name,
                    criterion_code=criterion.criterion_code,
                    criterion_parameters=criterion.criterion.parameters,
                    sample_size=size,
                    samples_count=self.ctx.samples_count,
                )

                if times:
                    mean = float(np.mean(times))
                    stats.add_criterion_statistic(criterion.criterion_code, size, mean)

        return stats

    def _get_times_from_storage(
        self,
        experiment_name: str,
        criterion_code: str,
        criterion_parameters: NumericParameters,
        sample_size: int,
        samples_count: int,
    ) -> list[float]:
        """
        Load execution time measurements from storage.

        Parameters
        ----------
        experiment_name : str
            Experiment name.
        criterion_code : str
            Criterion identifier.
        criterion_parameters : NumericParameters
            Criterion parameters.
        sample_size : int
            Sample size.
        samples_count : int
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
            experiment_name=experiment_name,
            criterion_code=criterion_code,
            criterion_parameters=criterion_parameters,
            sample_size=sample_size,
            samples_count=samples_count,
        )

        result = self.result_storage.get_data(query)
        if result is None:
            raise ValueError(f"Times for query {query} not found.")

        times = result.results_times

        return times
