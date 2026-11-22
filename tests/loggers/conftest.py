"""Shared fixtures for logging tests.

``logging.config.dictConfig`` and direct root-logger mutations change
process-global state; the fixture below snapshots and restores handlers,
levels and disabled flags around each test.
"""

import logging
from collections.abc import Iterator

import pytest


@pytest.fixture
def preserve_logging_state() -> Iterator[None]:
    """Snapshot and restore global logging state around a test."""
    root = logging.root
    old_root_level = root.level
    old_root_handlers = root.handlers[:]
    old_loggers = {
        name: (existing.level, existing.disabled, existing.handlers[:], existing.propagate)
        for name, existing in logging.Logger.manager.loggerDict.items()
        if isinstance(existing, logging.Logger)
    }

    yield

    root.setLevel(old_root_level)
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    for handler in old_root_handlers:
        root.addHandler(handler)

    for name, (level, disabled, handlers, propagate) in old_loggers.items():
        existing = logging.getLogger(name)
        existing.setLevel(level)
        existing.disabled = disabled
        for handler in existing.handlers[:]:
            existing.removeHandler(handler)
        for handler in handlers:
            existing.addHandler(handler)
        existing.propagate = propagate
