from dataclasses import dataclass

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

    def execute(self) -> TimeComplexityWorkerResult:
        pass
