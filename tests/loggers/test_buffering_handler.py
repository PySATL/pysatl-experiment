"""Tests for the custom buffering log handler."""

import logging
from logging.handlers import BufferingHandler
from unittest.mock import patch

import pytest

from pysatl_experiment.loggers.buffering_handler import FTBufferingHandler


class ExplodingBuffer:
    """Buffer double that fails on slicing to exercise the flush error path."""

    def __getitem__(self, item: object) -> object:
        """Fail on every access to emulate a broken buffer."""
        raise RuntimeError("slice failed")


def make_record(index: int) -> logging.LogRecord:
    """Build a log record that carries its index in the message."""
    return logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=index + 1,
        msg=f"record-{index}",
        args=(),
        exc_info=None,
    )


def fill_buffer(handler: FTBufferingHandler, count: int) -> None:
    """Append the given number of records directly to the handler buffer."""
    handler.buffer.extend(make_record(index) for index in range(count))


def buffered_messages(handler: FTBufferingHandler) -> list[str]:
    """Return messages of the records currently kept in the handler buffer."""
    return [record.getMessage() for record in handler.buffer]


# Checks that the handler subclasses the standard buffering handler.
def test_handler_extends_buffering_handler() -> None:
    assert issubclass(FTBufferingHandler, BufferingHandler)
    assert isinstance(FTBufferingHandler(10), BufferingHandler)


# Checks that the capacity passed to the constructor is stored unchanged.
@pytest.mark.parametrize("capacity", [0, 1, 2, 100])
def test_capacity_is_stored(capacity: int) -> None:
    assert FTBufferingHandler(capacity).capacity == capacity


# Checks that emitting records below capacity only appends them.
def test_emit_below_capacity_only_appends() -> None:
    handler = FTBufferingHandler(5)

    for index in range(3):
        handler.emit(make_record(index))

    assert buffered_messages(handler) == ["record-0", "record-1", "record-2"]


# Checks that reaching capacity triggers the custom flush which keeps recent records.
def test_emit_at_capacity_triggers_partial_flush() -> None:
    handler = FTBufferingHandler(4)

    for index in range(4):
        handler.emit(make_record(index))

    assert buffered_messages(handler) == ["record-2", "record-3"]


# Checks that flush keeps exactly the newest half of the configured capacity.
@pytest.mark.parametrize(
    ("capacity", "buffered", "expected"),
    [
        (8, 8, ["record-4", "record-5", "record-6", "record-7"]),
        (10, 10, ["record-5", "record-6", "record-7", "record-8", "record-9"]),
        (10, 6, ["record-1", "record-2", "record-3", "record-4", "record-5"]),
        (2, 2, ["record-1"]),
    ],
)
def test_flush_keeps_newest_half_of_capacity(capacity: int, buffered: int, expected: list[str]) -> None:
    handler = FTBufferingHandler(capacity)
    fill_buffer(handler, buffered)

    handler.flush()

    assert buffered_messages(handler) == expected


# Checks that flush rounds the retained count up for odd capacities.
@pytest.mark.parametrize(
    ("capacity", "expected"),
    [(5, ["record-3", "record-4"]), (7, ["record-4", "record-5", "record-6"])],
)
def test_flush_rounds_retained_count_up_for_odd_capacity(capacity: int, expected: list[str]) -> None:
    handler = FTBufferingHandler(capacity)
    fill_buffer(handler, capacity)

    handler.flush()

    assert buffered_messages(handler) == expected


# Checks that a capacity of one keeps every buffered record after a flush.
@pytest.mark.parametrize("buffered", [1, 3])
def test_flush_with_capacity_one_retains_all_records(buffered: int) -> None:
    handler = FTBufferingHandler(1)
    fill_buffer(handler, buffered)

    handler.flush()

    assert buffered_messages(handler) == [f"record-{index}" for index in range(buffered)]


# Checks that flushing an empty buffer leaves it empty.
@pytest.mark.parametrize("capacity", [1, 5, 100])
def test_flush_on_empty_buffer_keeps_buffer_empty(capacity: int) -> None:
    handler = FTBufferingHandler(capacity)

    handler.flush()

    assert handler.buffer == []


# Checks that flush keeps the very same record objects instead of copying them.
def test_flush_keeps_original_record_objects() -> None:
    handler = FTBufferingHandler(4)
    fill_buffer(handler, 4)
    newest = [record for record in handler.buffer][-2:]

    handler.flush()

    assert handler.buffer == newest


# Checks that flush is protected by an acquire/release pair on the handler lock.
def test_flush_acquires_and_releases_lock() -> None:
    handler = FTBufferingHandler(2)
    fill_buffer(handler, 2)

    with patch.object(handler, "acquire") as acquire, patch.object(handler, "release") as release:
        handler.flush()

    acquire.assert_called_once_with()
    release.assert_called_once_with()


# Checks that the lock is released even when slicing the buffer fails.
def test_flush_releases_lock_when_slicing_fails() -> None:
    handler = FTBufferingHandler(4)
    handler.buffer = ExplodingBuffer()  # type: ignore[assignment]

    with patch.object(handler, "release") as release:
        with pytest.raises(RuntimeError, match="slice failed"):
            handler.flush()

    release.assert_called_once_with()


# Checks that close flushes through the overridden partial flush implementation.
def test_close_flushes_through_custom_flush() -> None:
    handler = FTBufferingHandler(4)
    fill_buffer(handler, 4)

    handler.close()

    assert buffered_messages(handler) == ["record-2", "record-3"]
