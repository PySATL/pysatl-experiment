"""Bounded storage pages shared by bulk readers."""

from dataclasses import dataclass
from typing import Generic, TypeVar


M = TypeVar("M")


@dataclass(frozen=True)
class BulkBatch(Generic[M]):
    """Items ordered by id; next_after_id=None marks the end of traversal."""

    items: list[M]
    next_after_id: int | None
