"""Tests for logging verbosity helpers."""

import logging
from collections.abc import Iterator

import pytest

from pysatl_experiment.loggers import set_log_levels


BIAS_TESTER_LOGGER_NAMES: list[str] = getattr(set_log_levels, "__BIAS_TESTER_LOGGERS")
MODULE_LOGGER_NAME = "pysatl_experiment.loggers.set_log_levels"
UNRELATED_LOGGER_NAME = "pysatl_experiment.unrelated"


@pytest.fixture()
def restore_bias_tester_levels() -> Iterator[None]:
    """Restore bias tester logger levels to their initial values after each test."""
    saved = {name: logging.getLogger(name).level for name in BIAS_TESTER_LOGGER_NAMES}

    yield

    for name, level in saved.items():
        logging.getLogger(name).setLevel(level)


# Checks that the module targets exactly the documented bias tester logger namespace.
def test_module_declares_expected_bias_tester_loggers() -> None:
    assert BIAS_TESTER_LOGGER_NAMES == ["pysatl_experiment.resolvers"]


# Checks that reducing verbosity raises every targeted logger to WARNING.
@pytest.mark.parametrize("logger_name", BIAS_TESTER_LOGGER_NAMES)
def test_reduce_verbosity_sets_warning_level(logger_name: str, restore_bias_tester_levels: None) -> None:
    set_log_levels.reduce_verbosity_for_bias_tester()

    assert logging.getLogger(logger_name).level == logging.WARNING


# Checks that reducing verbosity returns None.
def test_reduce_verbosity_returns_none(restore_bias_tester_levels: None) -> None:
    assert set_log_levels.reduce_verbosity_for_bias_tester() is None  # type: ignore[func-returns-value]


# Checks that reducing verbosity reports the change through its own module logger.
def test_reduce_verbosity_logs_info_message(
    caplog: pytest.LogCaptureFixture,
    restore_bias_tester_levels: None,
) -> None:
    with caplog.at_level(logging.INFO, logger=MODULE_LOGGER_NAME):
        set_log_levels.reduce_verbosity_for_bias_tester()

    assert caplog.records[0].name == MODULE_LOGGER_NAME
    assert [record.getMessage() for record in caplog.records] == ["Reducing verbosity for bias tester."]


# Checks that unrelated loggers keep their level untouched while reducing verbosity.
def test_reduce_verbosity_leaves_unrelated_loggers_untouched(restore_bias_tester_levels: None) -> None:
    unrelated = logging.getLogger(UNRELATED_LOGGER_NAME)
    unrelated.setLevel(logging.DEBUG)

    try:
        set_log_levels.reduce_verbosity_for_bias_tester()

        assert unrelated.level == logging.DEBUG
    finally:
        unrelated.setLevel(logging.NOTSET)


# Checks that reducing verbosity overrides an explicitly configured debug level.
@pytest.mark.parametrize("initial_level", [logging.DEBUG, logging.ERROR])
def test_reduce_verbosity_overrides_configured_level(initial_level: int, restore_bias_tester_levels: None) -> None:
    logger = logging.getLogger(BIAS_TESTER_LOGGER_NAMES[0])
    logger.setLevel(initial_level)

    set_log_levels.reduce_verbosity_for_bias_tester()

    assert logger.level == logging.WARNING


# Checks that reducing verbosity twice gives the same warning level.
def test_reduce_verbosity_is_idempotent(restore_bias_tester_levels: None) -> None:
    set_log_levels.reduce_verbosity_for_bias_tester()
    set_log_levels.reduce_verbosity_for_bias_tester()

    for name in BIAS_TESTER_LOGGER_NAMES:
        assert logging.getLogger(name).level == logging.WARNING


# Checks that restoring verbosity resets every targeted logger to NOTSET.
@pytest.mark.parametrize("logger_name", BIAS_TESTER_LOGGER_NAMES)
def test_restore_verbosity_resets_level_to_notset(logger_name: str, restore_bias_tester_levels: None) -> None:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

    set_log_levels.restore_verbosity_for_bias_tester()

    assert logging.getLogger(logger_name).level == logging.NOTSET


# Checks that restoring verbosity returns None.
def test_restore_verbosity_returns_none(restore_bias_tester_levels: None) -> None:
    assert set_log_levels.restore_verbosity_for_bias_tester() is None  # type: ignore[func-returns-value]


# Checks that restoring verbosity reports the change through its own module logger.
def test_restore_verbosity_logs_info_message(
    caplog: pytest.LogCaptureFixture,
    restore_bias_tester_levels: None,
) -> None:
    with caplog.at_level(logging.INFO, logger=MODULE_LOGGER_NAME):
        set_log_levels.restore_verbosity_for_bias_tester()

    assert caplog.records[0].name == MODULE_LOGGER_NAME
    assert [record.getMessage() for record in caplog.records] == ["Restoring log verbosity."]


# Checks that restoring verbosity leaves unrelated loggers untouched.
def test_restore_verbosity_leaves_unrelated_loggers_untouched(restore_bias_tester_levels: None) -> None:
    unrelated = logging.getLogger(UNRELATED_LOGGER_NAME)
    unrelated.setLevel(logging.DEBUG)

    try:
        set_log_levels.restore_verbosity_for_bias_tester()

        assert unrelated.level == logging.DEBUG
    finally:
        unrelated.setLevel(logging.NOTSET)


# Checks that a reduce followed by a restore brings loggers back to the default level.
def test_reduce_then_restore_roundtrip(restore_bias_tester_levels: None) -> None:
    for name in BIAS_TESTER_LOGGER_NAMES:
        assert logging.getLogger(name).level == logging.NOTSET

    set_log_levels.reduce_verbosity_for_bias_tester()
    set_log_levels.restore_verbosity_for_bias_tester()

    for name in BIAS_TESTER_LOGGER_NAMES:
        assert logging.getLogger(name).level == logging.NOTSET


# Checks that verbosity changes apply to the very logger instance from the logging registry.
def test_verbosity_changes_apply_to_registry_logger_instances(restore_bias_tester_levels: None) -> None:
    logger = logging.getLogger(BIAS_TESTER_LOGGER_NAMES[0])

    set_log_levels.reduce_verbosity_for_bias_tester()
    assert logger.level == logging.WARNING

    set_log_levels.restore_verbosity_for_bias_tester()
    assert logger.level == logging.NOTSET
