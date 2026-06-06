"""
Logging subsystem configuration and initialization utilities.

This module contains the central logging configuration used throughout
PySatl. It provides helper functions for creating logging configurations,
configuring log levels, registering handlers and formatters, and
initializing logging during application startup.

Logging initialization is performed in two stages:

1. Early initialization through ``setup_logging_pre()``, which enables
   basic console logging before configuration files are loaded.
2. Full initialization through ``setup_logging()``, which applies user
   configuration and registers all required handlers.
"""

import logging
import logging.config
from copy import deepcopy
from typing import Any

from pysatl_experiment.constants import Config


logger = logging.getLogger(__name__)
LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
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


def setup_logging(config: Config, level: int | str | None = None, filename: str | None = None) -> None:
    """
    Perform complete logging initialization.

    Applies logging configuration, registers required handlers,
    configures verbosity levels and enables optional colorized output.

    Parameters
    ----------
    config : Config
        Application configuration.
    level : int or str or None, optional
        Log level.
    filename : str or None, optional
        Log file name.

    Notes
    -----
    This function should be executed after application configuration
    has been fully loaded.

    Logging initialization may be skipped during test execution unless
    explicitly requested through configuration.
    """
    if filename:
        log_config = deepcopy(LOGGING_CONFIG)
        log_config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": filename,
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "standard",
        }
        log_config["root"]["handlers"].append("file")
    else:
        log_config = config.get("log_config", deepcopy(LOGGING_CONFIG))

    handlers = log_config.get("handlers")
    if level and isinstance(handlers, dict):
        for name, handler in handlers.items():
            handler["level"] = level

    logging.config.dictConfig(log_config)
