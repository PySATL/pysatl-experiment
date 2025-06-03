from dataclasses import dataclass

from stattest.worker.model.abstract_worker.abstract_worker import IWorker, WorkerResult


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

    def execute(self) -> CriticalValueWorkerResult:
        pass
