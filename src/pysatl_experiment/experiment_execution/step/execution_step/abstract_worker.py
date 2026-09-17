"""
Abstract worker interface module.

This module defines the base abstraction for all worker implementations
used in the experiment execution pipeline.

Workers are responsible for performing computations on generated sample
data and returning structured results.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar


@dataclass
class WorkerResult:
    """
    Base class for all worker results.

    This class serves as a marker and base container for structured
    outputs returned by worker implementations.
    """


R = TypeVar("R", covariant=True, bound=WorkerResult)


class IWorker(Generic[R], ABC):
    """
    Abstract interface for all workers.

    Defines a unified contract for executing computational tasks
    over sample data.

    Parameters
    ----------
    Generic[R] : TypeVar
        Covariant result type bound to WorkerResult.
    """

    @abstractmethod
    def execute(self) -> R:
        """
        Execute worker computation.

        Returns
        -------
        R
            Computation result produced by the worker.
        """
        pass
