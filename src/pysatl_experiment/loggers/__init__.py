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
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "formatter": "standard",
        }
    },
    "root": {
        "handlers": ["console"],
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
        file_handler: dict[str, Any] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": filename,
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        }
        # Only reference the standard formatter when it is actually defined
        # (it is absent from arbitrary user-supplied configurations).
        if "standard" in log_config.get("formatters", {}):
            file_handler["formatter"] = "standard"
        handlers["file"] = file_handler
        log_config.setdefault("root", {}).setdefault("handlers", []).append("file")

    if level:
        handlers = log_config.get("handlers")
        if isinstance(handlers, dict):
            for handler in handlers.values():
                handler["level"] = level
        log_config.setdefault("root", {})["level"] = level

    logging.config.dictConfig(log_config)
