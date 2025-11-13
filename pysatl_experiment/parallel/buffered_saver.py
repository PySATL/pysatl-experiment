from typing import Generic, TypeVar
from collections.abc import Callable
import time

T = TypeVar("T")


class BufferedSaver(Generic[T]):
    """
    Generic buffered saver with adaptive flushing.
    """

    def __init__(
            self,
            save_func: Callable[[list[T]], None],
            buffer_size: int = 10,
            max_delay_seconds: float = 5.0,
    ):
        if buffer_size < 1:
            raise ValueError("buffer_size must be at least 1")
        self.save_func = save_func
        self.buffer_size = buffer_size
        self.max_delay = max_delay_seconds
        self.buffer: list[T] = []
        self.last_flush = time.time()

    def add(self, item: T) -> None:
        """
        Add item to buffer and flush if needed.
        """

        self.buffer.append(item)
        now = time.time()

        if len(self.buffer) >= self.buffer_size or (now - self.last_flush) >= self.max_delay:
            self.flush()

    def flush(self) -> None:
        """
        Force flush buffer.
        """

        if self.buffer:
            self.save_func(self.buffer)
            self.buffer.clear()
            self.last_flush = time.time()