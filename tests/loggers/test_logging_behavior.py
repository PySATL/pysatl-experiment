"""Behavioral tests for logging setup on the real logging infrastructure.

Unlike ``test_log_setup.py`` (which mocks ``dictConfig`` and checks the
configuration shape), these tests apply the configuration for real and
assert that log records actually flow to their destinations.

Because ``logging.config.dictConfig`` mutates process-global state, every
test uses the ``preserve_logging_state`` fixture to restore handlers,
levels and disabled flags afterwards.
"""

import json
import logging

import pytest

from pysatl_experiment.loggers import setup_logging


@pytest.fixture
def preserve_logging_state():
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


@pytest.mark.usefixtures("preserve_logging_state")
def test_debug_records_reach_stderr(capsys):
    """Regression test: DEBUG records must pass filtering after setup.

    Previously the level was applied to handlers only, leaving the root
    logger at WARNING and silently dropping DEBUG/INFO records.
    """
    setup_logging({}, level="DEBUG")

    logging.getLogger("pysatl_experiment.behavior_probe").debug("debug probe message")

    captured = capsys.readouterr()
    assert "debug probe message" in captured.err


@pytest.mark.usefixtures("preserve_logging_state")
def test_preexisting_logger_survives_setup(capsys):
    """Regression test: loggers created before setup must stay enabled.

    Previously dictConfig defaulted to disable_existing_loggers=True,
    which disabled module loggers created at import time before setup.
    """
    preexisting = logging.getLogger("pysatl_experiment.preexisting_probe")
    preexisting.info("warmup")  # ensure the logger is registered before setup

    setup_logging({})

    assert not preexisting.disabled

    preexisting.warning("preexisting warning probe")
    captured = capsys.readouterr()
    assert "preexisting warning probe" in captured.err


@pytest.mark.usefixtures("preserve_logging_state")
def test_file_handler_writes_message_and_traceback(tmp_path):
    log_file = tmp_path / "exp.log"

    setup_logging({}, filename=str(log_file))

    probe = logging.getLogger("pysatl_experiment.file_probe")
    try:
        raise ValueError("boom-probe")
    except ValueError:
        probe.exception("file probe failure")

    for handler in logging.root.handlers:
        handler.flush()

    content = log_file.read_text(encoding="utf-8")
    assert "file probe failure" in content
    assert "ValueError: boom-probe" in content


@pytest.mark.usefixtures("preserve_logging_state")
def test_file_handler_writes_json_lines(tmp_path):
    """File logs must be machine-readable JSON records."""
    log_file = tmp_path / "exp_json.log"

    setup_logging({}, filename=str(log_file))

    logging.getLogger("pysatl_experiment.json_probe").warning("json probe message")

    for handler in logging.root.handlers:
        handler.flush()

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    payload = json.loads(lines[0])
    assert payload["message"] == "json probe message"
    assert payload["level"] == "WARNING"
    assert payload["logger"] == "pysatl_experiment.json_probe"
    assert "timestamp" in payload
