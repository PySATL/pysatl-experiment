"""Repeatable traversal of an exact selection through point-query storage."""

from collections.abc import Iterable, Iterator
from typing import Generic, Protocol, TypeVar


M = TypeVar("M")
Q = TypeVar("Q")
M_co = TypeVar("M_co", covariant=True)
Q_contra = TypeVar("Q_contra", contravariant=True)


class QueryStorage(Protocol[M_co, Q_contra]):
    """Read-only part of the storage contract used by the adapter."""

    def get_data(self, query: Q_contra) -> M_co | None:
        """Return the exact result, or None when it is missing."""
        ...


class QueryResults(Generic[M, Q]):
    """Read the requested records afresh on each traversal, rejecting omissions."""

    def __init__(self, storage: QueryStorage[M, Q], queries: Iterable[Q]) -> None:
        self.storage = storage
        self.queries = tuple(queries)

    def __iter__(self) -> Iterator[M]:
        """Yield complete records in query order without retaining a cursor."""
        for query in self.queries:
            result = self.storage.get_data(query)
            if result is None:
                raise ValueError(f"Missing report result: {query}")
            yield result
