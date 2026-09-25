"""Tests for the stderr stream logging handler."""

import logging
from collections.abc import Iterator
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pysatl_experiment.loggers import std_err_stream_handler
from pysatl_experiment.loggers.std_err_stream_handler import FTStdErrStreamHandler


def make_record(
    level: int = logging.INFO,
    msg: object = "hello",
    name: str = "test_logger",
    args: tuple = (),
) -> logging.LogRecord:
    """Build a log record with sensible defaults for handler tests."""
    return logging.LogRecord(
        name=name,
        level=level,
        pathname=__file__,
        lineno=21,
        msg=msg,
        args=args,
        exc_info=None,
    )


def install_stderr(monkeypatch: pytest.MonkeyPatch, stream: object) -> None:
    """Point the stderr reference used by the handler module at the given stream."""
    monkeypatch.setattr(std_err_stream_handler, "sys", SimpleNamespace(stderr=stream))


@pytest.fixture()
def fake_stderr(monkeypatch: pytest.MonkeyPatch) -> Iterator[StringIO]:
    """Replace the stderr stream used by the handler module with an in-memory stream."""
    stream = StringIO()
    install_stderr(monkeypatch, stream)

    yield stream


# Checks that the handler subclasses the standard logging handler.
def test_handler_extends_logging_handler() -> None:
    assert issubclass(FTStdErrStreamHandler, logging.Handler)
    assert isinstance(FTStdErrStreamHandler(), logging.Handler)


# Checks that emitting writes the record message followed by a newline.
def test_emit_writes_message_with_trailing_newline(fake_stderr: StringIO) -> None:
    FTStdErrStreamHandler().emit(make_record(msg="hello"))

    assert fake_stderr.getvalue() == "hello\n"


# Checks that a configured formatter controls the written line.
def test_emit_uses_configured_formatter(fake_stderr: StringIO) -> None:
    handler = FTStdErrStreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))

    handler.emit(make_record(msg="hello"))

    assert fake_stderr.getvalue() == "INFO:test_logger:hello\n"


# Checks that message arguments are interpolated before writing.
def test_emit_interpolates_message_arguments(fake_stderr: StringIO) -> None:
    FTStdErrStreamHandler().emit(make_record(msg="hello %s", args=("world",)))

    assert fake_stderr.getvalue() == "hello world\n"


# Checks that every record is written on its own line.
def test_emit_writes_each_record_on_its_own_line(fake_stderr: StringIO) -> None:
    handler = FTStdErrStreamHandler()

    handler.emit(make_record(msg="first"))
    handler.emit(make_record(msg="second"))

    assert fake_stderr.getvalue() == "first\nsecond\n"


# Checks that records really end up on the global stderr stream.
def test_emit_writes_to_global_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    FTStdErrStreamHandler().emit(make_record(msg="hello"))

    assert capsys.readouterr().err == "hello\n"


# Checks that emitting reports the record through the handler flush method.
def test_emit_flushes_after_writing(fake_stderr: StringIO) -> None:
    handler = FTStdErrStreamHandler()

    with patch.object(handler, "flush") as flush:
        handler.emit(make_record())

    flush.assert_called_once_with()


# Checks that emitting returns None on a successful write.
def test_emit_returns_none(fake_stderr: StringIO) -> None:
    assert FTStdErrStreamHandler().emit(make_record()) is None


# Checks that the handler keeps no reference to the stderr stream between calls.
def test_emit_does_not_keep_stderr_reference(fake_stderr: StringIO) -> None:
    handler = FTStdErrStreamHandler()

    handler.emit(make_record())

    assert not any(value is fake_stderr for value in vars(handler).values())


# Checks that flush flushes the current stderr stream.
def test_flush_flushes_stderr_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    stream = MagicMock()
    install_stderr(monkeypatch, stream)

    FTStdErrStreamHandler().flush()

    stream.flush.assert_called_once_with()


# Checks that flush is protected by an acquire/release pair on the handler lock.
def test_flush_acquires_and_releases_lock() -> None:
    handler = FTStdErrStreamHandler()

    with patch.object(handler, "acquire") as acquire, patch.object(handler, "release") as release:
        handler.flush()

    acquire.assert_called_once_with()
    release.assert_called_once_with()


# Checks that the lock is released even when flushing stderr fails.
def test_flush_releases_lock_when_stderr_flush_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    stream = MagicMock()
    stream.flush.side_effect = OSError("flush failed")
    install_stderr(monkeypatch, stream)
    handler = FTStdErrStreamHandler()

    with patch.object(handler, "release") as release:
        with pytest.raises(OSError, match="flush failed"):
            handler.flush()

    release.assert_called_once_with()


# Checks that recursion errors are re-raised instead of being swallowed.
def test_emit_reraises_recursion_error(fake_stderr: StringIO) -> None:
    handler = FTStdErrStreamHandler()

    with (
        patch.object(handler, "format", side_effect=RecursionError),
        patch.object(
            handler,
            "handleError",
        ) as handle_error,
    ):
        with pytest.raises(RecursionError):
            handler.emit(make_record())

    handle_error.assert_not_called()


# Checks that a failing format step is reported through handleError.
def test_emit_handles_format_failure(fake_stderr: StringIO) -> None:
    handler = FTStdErrStreamHandler()
    record = make_record()

    with (
        patch.object(handler, "format", side_effect=ValueError("format failed")),
        patch.object(
            handler,
            "handleError",
        ) as handle_error,
    ):
        handler.emit(record)

    handle_error.assert_called_once_with(record)


# Checks that a failing stderr write is reported through handleError.
def test_emit_handles_write_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    stream = MagicMock()
    stream.write.side_effect = OSError("write failed")
    install_stderr(monkeypatch, stream)
    handler = FTStdErrStreamHandler()
    record = make_record()

    with patch.object(handler, "handleError") as handle_error:
        handler.emit(record)

    handle_error.assert_called_once_with(record)


# Checks that a failing flush inside emit is reported through handleError.
def test_emit_handles_flush_failure(fake_stderr: StringIO) -> None:
    handler = FTStdErrStreamHandler()
    record = make_record()

    with (
        patch.object(handler, "flush", side_effect=OSError("flush failed")),
        patch.object(
            handler,
            "handleError",
        ) as handle_error,
    ):
        handler.emit(record)

    handle_error.assert_called_once_with(record)


# Checks that the handler writes the records of a logger it is attached to.
def test_handler_writes_records_of_attached_logger(capsys: pytest.CaptureFixture[str]) -> None:
    handler = FTStdErrStreamHandler()
    logger = logging.getLogger("pysatl_experiment.tests.stderr_handler")
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)

    try:
        logger.warning("warning message")
    finally:
        logger.removeHandler(handler)
        logger.setLevel(logging.NOTSET)

    assert capsys.readouterr().err.endswith("warning message\n")
