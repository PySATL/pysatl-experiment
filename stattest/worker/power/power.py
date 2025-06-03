from dataclasses import dataclass

from stattest.worker.model.abstract_worker.abstract_worker import WorkerResult, IWorker


@dataclass
class PowerWorkerResult(WorkerResult):
    """
    Power worker result container.
    """
    results_criteria: list[bool]


class PowerWorker(IWorker[PowerWorkerResult]):
    """
    Power worker.
    """
    def execute(self) -> PowerWorkerResult:
        pass
