from dataclasses import dataclass
from time import perf_counter

from pysatl_criterion.statistics.goodness_of_fit import AbstractGoodnessOfFitStatistic
from stattest.worker.model.abstract_worker.abstract_worker import IWorker, WorkerResult


@dataclass
class TimeComplexityWorkerResult(WorkerResult):
    """
    Time complexity worker result container.
    """

    results_times: list[float]


class TimeComplexityWorker(IWorker[TimeComplexityWorkerResult]):
    """
    Time complexity worker.
    """

    def __init__(self, statistics: AbstractGoodnessOfFitStatistic, sample_data: list[list[float]]):
        self.statistics = statistics
        self.sample_data = sample_data

    def execute(self) -> TimeComplexityWorkerResult:
        """
        Execute critical value worker.
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
