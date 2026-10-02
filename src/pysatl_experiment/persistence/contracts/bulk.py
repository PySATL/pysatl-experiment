"""Common contract for bounded bulk storage operations."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from pysatl_criterion.persistence.models.base import IStorage

from pysatl_experiment.persistence.models.bulk import BulkBatch


M = TypeVar("M")
Q = TypeVar("Q", contravariant=True)


class IBulkDataStorage(IStorage, Generic[M, Q], ABC):
    """Read and write bounded batches without loading the entire dataset."""

    @abstractmethod
    def bulk_insert(self, data: Iterable[M], *, batch_size: int = 1000) -> None:
        """Write atomic batches; earlier batches survive a later failure.

        Concrete stores define whether duplicate keys append or update records.
        """

    @abstractmethod
    def read_bulk(self, query: Q, *, after_id: int | None = None, batch_size: int = 1000) -> BulkBatch[M]:
        """Read at most batch_size items in ascending id order after after_id.

        Traversal assumes the dataset remains unchanged. A full final page may
        require one additional empty read to discover the end.
        """
