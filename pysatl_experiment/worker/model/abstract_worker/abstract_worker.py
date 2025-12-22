from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar


@dataclass
class WorkerResult:
    """
    Worker result base container.
    """


R = TypeVar("R", covariant=True, bound=WorkerResult)


class IWorker(Generic[R], ABC):
    """
    Worker interface.
    """

    @abstractmethod
    def execute(self) -> R:
        """
        Execute worker.
        """
        pass
