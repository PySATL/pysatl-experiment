from dataclasses import dataclass

from line_profiler import profile

from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic
from pysatl_experiment.worker.model.abstract_worker.abstract_worker import IWorker, WorkerResult


@dataclass
class CriticalValueWorkerResult(WorkerResult):
    """
    Critical value worker result container.
    """

    results_statistics: list[float]


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

        results_statistics = []
        for data in self.sample_data:
            statistics_value = self.statistics.execute_statistic(rvs=data)
            results_statistics.append(statistics_value)

        result = CriticalValueWorkerResult(results_statistics=results_statistics)

        return result
