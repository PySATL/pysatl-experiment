"""Bulk traversal kept separate from storage queries and transactions."""

from collections.abc import Iterator
from typing import Generic, TypeVar

from pysatl_experiment.persistence.contracts.bulk import IBulkDataStorage
from pysatl_experiment.persistence.validation import require_positive_integer


M = TypeVar("M")
Q = TypeVar("Q")


class BulkDataIterator(Iterator[M], Generic[M, Q]):
    """Lazily yield items from bounded pages of a dataset kept unchanged during traversal."""

    def __init__(
        self,
        storage: IBulkDataStorage[M, Q],
        query: Q,
        *,
        batch_size: int = 1000,
        limit: int | None = None,
    ):
        require_positive_integer(batch_size, "batch_size")
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 0):
            raise ValueError("limit must be a nonnegative integer or None")
        self._storage = storage
        self._query = query
        self._batch_size = batch_size
        self._remaining = limit
        self._after_id: int | None = None
        self._batch: Iterator[M] = iter(())
        self._finished = limit == 0

    def __iter__(self) -> "BulkDataIterator[M, Q]":
        """Return this single-pass iterator."""
        return self

    def __next__(self) -> M:
        """Return one item, loading a new page only when needed."""
        try:
            item = next(self._batch)
        except StopIteration:
            if self._finished:
                raise
            size = self._batch_size if self._remaining is None else min(self._batch_size, self._remaining)
            batch = self._storage.read_bulk(self._query, after_id=self._after_id, batch_size=size)
            self._after_id = batch.next_after_id
            self._finished = self._after_id is None or not batch.items
            self._batch = iter(batch.items)
            item = next(self._batch)
        if self._remaining is not None:
            self._remaining -= 1
            if self._remaining == 0:
                self._finished = True
        return item
