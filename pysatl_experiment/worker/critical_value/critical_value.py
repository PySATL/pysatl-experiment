import time
from dataclasses import dataclass

from line_profiler import profile
from numpy import float64

from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic
from pysatl_experiment.worker.model.abstract_worker.abstract_worker import IWorker, WorkerResult


@dataclass
class CriticalValueWorkerResult(WorkerResult):
    """
    Critical value worker result container.
    """

    results_statistics: list[float | float64]


class CriticalValueWorker(IWorker[CriticalValueWorkerResult]):
    """
    Critical value worker.
    """

    def __init__(self, statistics: AbstractGoodnessOfFitStatistic, sample_data: list[list[float]]):
        self.statistics = statistics
        self.sample_data = sample_data

    @profile
    def execute(self) -> CriticalValueWorkerResult:
        """
        Execute critical value worker.
        """

        results_statistics = [self.statistics.execute_statistic(rvs=data) for data in self.sample_data]

        result = CriticalValueWorkerResult(results_statistics=results_statistics)

        return result
