"""
Logging subsystem configuration and initialization utilities.

This module contains the central logging configuration used throughout
PySatl. It provides the default logging configuration and the
``setup_logging()`` entry point used during application startup.

Logging is initialized once the application configuration has been
loaded: ``setup_logging()`` applies either the user-supplied
``log_config`` mapping or the built-in default, optionally adds a
rotating file handler and applies the requested verbosity level.
"""

import logging
import logging.config
import sys
from copy import deepcopy
from typing import Any


logger = logging.getLogger(__name__)
LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    # Keep loggers created before setup (e.g. at module import time)
    # enabled; dictConfig disables them otherwise.
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": LOGFORMAT},
    },
    "handlers": {
        "console": {
            "class": "pysatl_experiment.loggers.rich_handler.FtRichHandler",
        }
    },
    "root": {
        "handlers": ["console"],
    },
    # Keep noisy third-party loggers at WARNING even when the root level
    # is lowered (e.g. via --log-level DEBUG).
    "loggers": {
        "matplotlib": {"level": "WARNING"},
        "PIL": {"level": "WARNING"},
        "numexpr": {"level": "WARNING"},
    },
}


def setup_logging(config: Any, level: int | str | None = None, filename: str | None = None) -> None:
    """
    Perform complete logging initialization.

    Applies logging configuration, registers required handlers and
    configures verbosity levels.

    The base configuration is taken from the ``log_config`` key of the
    application configuration when present, otherwise the built-in
    default configuration is used. When ``filename`` is given, a
    rotating file handler is added on top of the base configuration.

    Parameters
    ----------
    config : Config
        Application configuration.
    level : int or str or None, optional
        Log level. Applied both to handlers and to the root logger so
        that records of the requested verbosity actually pass filtering.
    filename : str or None, optional
        Log file name.

    Notes
    -----
    This function should be executed after application configuration
    has been fully loaded.

    Logging initialization may be skipped during test execution unless
    explicitly requested through configuration.
    """
    log_config = deepcopy(config.get("log_config") or LOGGING_CONFIG)

    if filename:
        handlers = log_config.setdefault("handlers", {})
        formatters = log_config.setdefault("formatters", {})
        # File logs are JSON-formatted for machine processing; the console
        # output stays human-readable.
        formatters.setdefault("json", {"()": "pysatl_experiment.loggers.json_formatter.JsonFormatter"})
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": filename,
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "json",
        }
        log_config.setdefault("root", {}).setdefault("handlers", []).append("file")

    if level:
        handlers = log_config.get("handlers")
        if isinstance(handlers, dict):
            for handler in handlers.values():
                handler["level"] = level
        log_config.setdefault("root", {})["level"] = level

    logging.config.dictConfig(log_config)


def setup_exception_logging() -> None:
    """
    Route uncaught exceptions into the logging system.

    Installs a ``sys.excepthook`` that logs uncaught exceptions at
    CRITICAL level with a full traceback, so crashes leave a trace in
    configured log destinations (e.g. the log file) instead of only
    appearing on stderr.

    Notes
    -----
    ``KeyboardInterrupt`` is still delegated to the default hook so
    that interactive interruption keeps its standard behavior.
    """
    exception_logger = logging.getLogger("pysatl_experiment")

    def _log_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        exception_logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = _log_uncaught_exception
