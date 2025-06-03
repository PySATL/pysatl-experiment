from dataclasses import dataclass
from typing import TypeVar, Protocol


@dataclass
class WorkerResult:
    """
    Worker result base container.
    """

R = TypeVar("R", covariant=True, bound=WorkerResult)

class IWorker(Protocol[R]):
    """
    Worker interface.
    """
    def execute(self) -> R:
        """
        Execute worker.
        """
        pass
