"""
Critical value computation worker module.

This module provides an implementation of a worker that computes
statistical values for a set of samples using a specified
goodness-of-fit statistic.
"""

from dataclasses import dataclass

from line_profiler import profile
from numpy import float64
from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic

from pysatl_experiment.worker.model.abstract_worker.abstract_worker import IWorker, WorkerResult


@dataclass
class CriticalValueWorkerResult(WorkerResult):
    """
    Result container for critical value worker.

    Attributes
    ----------
    results_statistics : list[float | numpy.float64]
        Computed statistic values for each sample.
    """

    results_statistics: list[float | float64]


class CriticalValueWorker(IWorker[CriticalValueWorkerResult]):
    """
    Worker for computing critical value statistics on generated samples.

    This worker applies a given goodness-of-fit statistic to each sample
    in the dataset and returns the computed statistic values.

    Parameters
    ----------
    statistics : AbstractGoodnessOfFitStatistic
        Statistical test or metric used to compute values on each sample.
    sample_data : list[list[float]]
        Collection of samples. Each inner list represents one dataset.

    Attributes
    ----------
    statistics : AbstractGoodnessOfFitStatistic
        Statistic instance used for computations.
    sample_data : list[list[float]]
        Input samples to process.
    """

    def __init__(self, statistics: AbstractGoodnessOfFitStatistic, sample_data: list[list[float]]):
        """
        Initialize worker.

        Parameters
        ----------
        statistics : AbstractGoodnessOfFitStatistic
            Statistic instance used for computation.
        sample_data : list[list[float]]
            Input datasets.
        """
        self.statistics = statistics
        self.sample_data = sample_data

    @profile
    def execute(self) -> CriticalValueWorkerResult:
        """
        Execute the critical value computation.

        Returns
        -------
        CriticalValueWorkerResult
            Object containing computed statistic values for all samples.
        """
        results_statistics = [self.statistics.execute_statistic(rvs=data) for data in self.sample_data]

        result = CriticalValueWorkerResult(results_statistics=results_statistics)

        return result
