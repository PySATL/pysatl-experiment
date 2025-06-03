from dataclasses import dataclass
from typing import Protocol, TypeVar


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
