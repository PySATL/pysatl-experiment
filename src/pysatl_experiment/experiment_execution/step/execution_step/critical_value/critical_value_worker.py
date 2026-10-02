"""
Critical value computation worker module.

This module provides an implementation of a worker that computes
statistical values for a set of samples using a specified
goodness-of-fit statistic.
"""

from dataclasses import dataclass

from line_profiler import profile
from numpy import float64
from pysatl_criterion.statistics import AbstractGoodnessOfFitStatistic

from pysatl_experiment.experiment_execution.step.execution_step.abstract_worker import IWorker, WorkerResult
from pysatl_experiment.types import SampleBatch


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
    sample_data : SampleBatch
        Collection of samples. Each inner list represents one dataset.

    Attributes
    ----------
    statistics : AbstractGoodnessOfFitStatistic
        Statistic instance used for computations.
    sample_data : SampleBatch
        Input samples to process.
    """

    def __init__(self, statistics: AbstractGoodnessOfFitStatistic, sample_data: SampleBatch):
        """
        Initialize worker.

        Parameters
        ----------
        statistics : AbstractGoodnessOfFitStatistic
            Statistic instance used for computation.
        sample_data : SampleBatch
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
        results_statistics = [
            self.statistics.execute_statistic(rvs=sample.values) for sample in self.sample_data.samples
        ]

        result = CriticalValueWorkerResult(results_statistics=results_statistics)

        return result
