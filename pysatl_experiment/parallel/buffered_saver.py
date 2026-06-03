"""Buffered batch-saving utilities."""

from collections.abc import Callable
from typing import Generic, TypeVar


T = TypeVar("T")


class BufferedSaver(Generic[T]):
    """
    Generic buffered saver with adaptive flushing.

    Parameters
    ----------
    save_func : Callable[[list[T]], None]
        Function used to persist buffered items.
    buffer_size : int, default=10
        Maximum number of items before automatic flush.
    """

    def __init__(
        self,
        save_func: Callable[[list[T]], None],
        buffer_size: int = 10,
    ) -> None:
        """
        Initialize buffered saver.

        Parameters
        ----------
        save_func : Callable[[list[T]], None]
            Function used to persist buffered items.
        buffer_size : int, default=10
            Maximum number of items before automatic flush.
        """
        if buffer_size < 1:
            raise ValueError("Size of buffer must be at least 1.")

        self.save_func = save_func
        self.buffer_size = buffer_size
        self.buffer: list[T] = []

    def add(self, item: T) -> None:
        """
        Add item to buffer.

        Buffer is automatically flushed when the configured
        buffer size is reached.

        Parameters
        ----------
        item : T
            Item to add.
        """
        self.buffer.append(item)

        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """Flush all buffered items."""
        if self.buffer:
            self.save_func(self.buffer[:])
            self.buffer.clear()
