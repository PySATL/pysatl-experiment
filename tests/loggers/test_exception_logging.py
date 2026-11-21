"""Tests for the uncaught exception logging hook."""

import logging
import sys

from pysatl_experiment.loggers import setup_exception_logging


# Checks that installing the hook replaces sys.excepthook.
def test_setup_exception_logging_installs_hook(monkeypatch) -> None:
    sentinel = lambda *args: None  # noqa: E731
    monkeypatch.setattr(sys, "excepthook", sentinel)

    setup_exception_logging()

    assert sys.excepthook is not sentinel
    assert callable(sys.excepthook)


# Checks that uncaught exceptions are logged at CRITICAL level with a traceback.
def test_hook_logs_uncaught_exception(monkeypatch, caplog) -> None:
    monkeypatch.setattr(sys, "excepthook", lambda *args: None)
    setup_exception_logging()

    try:
        raise RuntimeError("uncaught boom")
    except RuntimeError:
        exc_type, exc_value, exc_traceback = sys.exc_info()

    assert exc_type is not None
    assert exc_value is not None

    with caplog.at_level(logging.CRITICAL, logger="pysatl_experiment"):
        sys.excepthook(exc_type, exc_value, exc_traceback)

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelno == logging.CRITICAL
    assert record.message == "Uncaught exception"
    assert record.exc_info is not None
    assert isinstance(record.exc_info[1], RuntimeError)


# Checks that KeyboardInterrupt is delegated to the default hook instead of logging.
def test_hook_delegates_keyboard_interrupt(monkeypatch, caplog) -> None:
    delegated = []
    monkeypatch.setattr(sys, "__excepthook__", lambda *args: delegated.append(args))
    monkeypatch.setattr(sys, "excepthook", lambda *args: None)
    setup_exception_logging()

    with caplog.at_level(logging.CRITICAL, logger="pysatl_experiment"):
        sys.excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)

    assert len(delegated) == 1
    assert caplog.records == []
