"""Tests for the Rich based logging handler."""

import logging
import re
from io import StringIO
from unittest.mock import patch

import pytest
from rich._null_file import NullFile
from rich.console import Console

from pysatl_experiment.loggers.rich_handler import FtRichHandler


TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}(?!\d)")

LEVEL_NAMES = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def make_record(level: int = logging.INFO, msg: str = "hello", name: str = "test_logger") -> logging.LogRecord:
    """Build a log record with sensible defaults for handler tests."""
    return logging.LogRecord(
        name=name,
        level=level,
        pathname=__file__,
        lineno=13,
        msg=msg,
        args=(),
        exc_info=None,
    )


def make_console() -> tuple[Console, StringIO]:
    """Build a plain Console writing into an in-memory stream."""
    stream = StringIO()

    return Console(file=stream, force_terminal=False, no_color=True, width=200), stream


# Checks that the handler subclasses the standard logging handler.
def test_handler_extends_logging_handler() -> None:
    console, _ = make_console()

    assert issubclass(FtRichHandler, logging.Handler)
    assert isinstance(FtRichHandler(console), logging.Handler)


# Checks that the constructor stores the console used for rendering.
def test_init_stores_provided_console() -> None:
    console, _ = make_console()

    assert FtRichHandler(console)._console is console


# Checks that the constructor forwards remaining arguments to the base handler.
def test_init_forwards_arguments_to_base_handler() -> None:
    console, _ = make_console()

    handler = FtRichHandler(console, logging.CRITICAL)

    assert handler.level == logging.CRITICAL


# Checks that emitting writes the message, logger name and level to the console.
@pytest.mark.parametrize("level_name", LEVEL_NAMES)
def test_emit_writes_message_name_and_level(level_name: str) -> None:
    console, stream = make_console()
    handler = FtRichHandler(console)

    handler.emit(make_record(level=logging.getLevelName(level_name), msg="payload"))

    output = stream.getvalue()
    assert "payload" in output
    assert "test_logger" in output
    assert level_name in output


# Checks that the emitted line starts with a millisecond precision timestamp.
def test_emit_writes_timestamp_with_millisecond_precision() -> None:
    console, stream = make_console()
    handler = FtRichHandler(console)

    handler.emit(make_record())

    assert TIMESTAMP_PATTERN.match(stream.getvalue())


# Checks that the emitted line joins its parts with the gray separator.
def test_emit_joins_parts_with_separator() -> None:
    console, stream = make_console()
    handler = FtRichHandler(console)

    handler.emit(make_record(msg="payload"))

    assert stream.getvalue().count(" - ") == 3


# Checks that a configured formatter is used to render the record.
def test_emit_uses_configured_formatter() -> None:
    console, stream = make_console()
    handler = FtRichHandler(console)
    handler.setFormatter(logging.Formatter("%(message)s<end>"))

    handler.emit(make_record(msg="payload"))

    output = stream.getvalue()
    assert "payload<end>" in output
    assert "test_logger" in output


# Checks that emitting a record succeeds without raising an error.
def test_emit_returns_none_on_success() -> None:
    console, _ = make_console()

    assert FtRichHandler(console).emit(make_record()) is None


# Checks that the null file console skips printing and delegates to handleError.
def test_emit_skips_printing_for_null_file_console() -> None:
    console = Console(file=NullFile(), force_terminal=False)
    handler = FtRichHandler(console)

    with patch.object(handler, "handleError") as handle_error, patch.object(console, "print") as print_mock:
        handler.emit(make_record())

    print_mock.assert_not_called()
    handle_error.assert_called_once()
    assert isinstance(handle_error.call_args.args[0], logging.LogRecord)


# Checks that recursion errors are re-raised instead of being swallowed.
def test_emit_reraises_recursion_error() -> None:
    console, _ = make_console()
    handler = FtRichHandler(console)

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
def test_emit_handles_format_failure() -> None:
    console, _ = make_console()
    handler = FtRichHandler(console)
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


# Checks that a failing console print is reported through handleError.
def test_emit_handles_print_failure() -> None:
    console, _ = make_console()
    handler = FtRichHandler(console)
    record = make_record()

    with (
        patch.object(console, "print", side_effect=ValueError("print failed")),
        patch.object(
            handler,
            "handleError",
        ) as handle_error,
    ):
        handler.emit(record)

    handle_error.assert_called_once_with(record)
