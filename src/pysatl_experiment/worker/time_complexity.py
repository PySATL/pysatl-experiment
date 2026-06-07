"""
Time complexity measurement worker module.

This module implements a worker that benchmarks execution time
of a statistical function over multiple datasets.
"""

from dataclasses import dataclass
from time import perf_counter

from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic

from src.pysatl_experiment.worker.model.abstract_worker import IWorker, WorkerResult


@dataclass
class TimeComplexityWorkerResult(WorkerResult):
    """
    Result container for time complexity worker.

    Attributes
    ----------
    results_times : list[float]
        Execution times (in seconds) for each sample.
    """

    results_times: list[float]


class TimeComplexityWorker(IWorker[TimeComplexityWorkerResult]):
    """
    Worker for measuring computational time complexity of a statistic.

    This worker executes a statistical function on multiple samples and
    measures execution time for each run using a high-resolution timer.

    Parameters
    ----------
    statistics : AbstractGoodnessOfFitStatistic
        Statistic function to benchmark.
    sample_data : list[list[float]]
        Input samples used for timing measurements.

    Attributes
    ----------
    statistics : AbstractGoodnessOfFitStatistic
        Statistic being benchmarked.
    sample_data : list[list[float]]
        Input dataset for performance evaluation.
    """

    def __init__(self, statistics: AbstractGoodnessOfFitStatistic, sample_data: list[list[float]]):
        """
        Initialize time complexity worker.

        Parameters
        ----------
        statistics : AbstractGoodnessOfFitStatistic
            Statistic instance to benchmark.
        sample_data : list[list[float]]
            Input datasets.
        """
        self.statistics = statistics
        self.sample_data = sample_data

    def execute(self) -> TimeComplexityWorkerResult:
        """
        Measure execution time of the statistic over all samples.

        Returns
        -------
        TimeComplexityWorkerResult
            List of execution times (in seconds) for each sample.
        """
        results_times = []
        for data in self.sample_data:
            start = perf_counter()
            _ = self.statistics.execute_statistic(rvs=data)
            end = perf_counter()
            time = end - start
            results_times.append(time)

        result = TimeComplexityWorkerResult(results_times=results_times)

        return result
