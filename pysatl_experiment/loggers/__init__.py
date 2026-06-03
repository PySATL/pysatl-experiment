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
import os
from copy import deepcopy
from logging import Formatter
from pathlib import Path
from typing import Any

from pysatl_experiment.constants import Config
from pysatl_experiment.exceptions import OperationalException
from pysatl_experiment.loggers.buffering_handler import FTBufferingHandler
from pysatl_experiment.loggers.rich_console import get_rich_console
from pysatl_experiment.loggers.rich_handler import FtRichHandler


logger = logging.getLogger(__name__)
LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Initialize buffer handler - will be used for /log endpoints
bufferHandler = FTBufferingHandler(1000)
bufferHandler.setFormatter(Formatter(LOGFORMAT))

error_console = get_rich_console(stderr=True, color_system=None)


def get_existing_handlers(handler_type):
    """
    Find an existing root logger handler of the specified type.

    Searches through handlers registered on the root logger and returns
    the first handler that is an instance of the specified class.

    Parameters
    ----------
    handler_type : type
        Handler type to search for.

    Returns
    -------
    logging.Handler | None
        Matching handler instance if found, otherwise ``None``.

    Notes
    -----
    This helper is primarily used to avoid duplicate handler
    registration during repeated logging initialization.
    """
    return next((h for h in logging.root.handlers if isinstance(h, handler_type)), None)
    # TODO: add explicit typing for handler classes and return values


def setup_logging_pre() -> None:
    """
    Perform preliminary logging initialization.

    Configures a minimal logging environment that can be used before
    application configuration has been loaded. At this stage only
    console output and in-memory buffering are enabled.

    Notes
    -----
    Early log messages are not automatically propagated to handlers
    configured during full initialization.

    This function is intended to be called during application startup
    before configuration parsing occurs.
    """
    rh = FtRichHandler(console=error_console)
    rh.setFormatter(Formatter("%(message)s"))
    logging.basicConfig(
        level=logging.INFO,
        format=LOGFORMAT,
        handlers=[
            # FTStdErrStreamHandler(),
            rh,
            bufferHandler,
        ],
    )
    # TODO: investigate whether early log records should be replayed to
    #  newly configured handlers during full initialization.


FT_LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    # "incremental": True,
    # "disable_existing_loggers": False,
    "formatters": {
        "basic": {"format": "%(message)s"},
        "standard": {
            "format": LOGFORMAT,
        },
    },
    "handlers": {
        "console": {
            "class": "pysatl_experiment.loggers.rich_handler.FtRichHandler",
            "formatter": "basic",
        },
    },
    "root": {
        "handlers": [
            "console",
            # "file",
        ],
        "level": "INFO",
    },
}


def _set_log_levels(log_config: dict[str, Any], verbosity: int = 0, api_verbosity: str = "info") -> None:
    """
    Configure log levels for application and third-party loggers.

    Updates the logging configuration dictionary with default log levels
    for internal and external libraries according to the selected
    verbosity settings.

    Parameters
    ----------
    log_config : dict[str, Any]
        Logging configuration dictionary.
    verbosity : int, default=0
        Application verbosity level.
    api_verbosity : str, default="info"
        Verbosity level used by the API server.

    Notes
    -----
    Existing logger configurations are preserved.

    Logger entries are added only when no explicit configuration is
    already present.
    """
    if "loggers" not in log_config:
        log_config["loggers"] = {}

    # Set default levels for third party libraries
    third_party_loggers = {
        "pysatl_experiment": logging.INFO if verbosity <= 1 else logging.DEBUG,
        "requests": logging.INFO if verbosity <= 1 else logging.DEBUG,
        "urllib3": logging.INFO if verbosity <= 1 else logging.DEBUG,
        "httpcore": logging.INFO if verbosity <= 1 else logging.DEBUG,
        "ccxt.base.exchange": logging.INFO if verbosity <= 2 else logging.DEBUG,
        "telegram": logging.INFO,
        "httpx": logging.WARNING,
        "werkzeug": logging.ERROR if api_verbosity == "error" else logging.INFO,
    }

    # TODO: Extract third-party logger definitions into a dedicated
    #  configuration constant?

    # Add third party loggers to the configuration
    for logger_name, level in third_party_loggers.items():
        if logger_name not in log_config["loggers"]:
            log_config["loggers"][logger_name] = {
                "level": logging.getLevelName(level),
                "propagate": True,
            }


def _add_root_handler(log_config: dict[str, Any], handler_name: str):
    """
    Register a handler on the root logger configuration.

    Parameters
    ----------
    log_config : dict[str, Any]
        Logging configuration dictionary.
    handler_name : str
        Name of the handler to register.

    Notes
    -----
    Duplicate handler registrations are ignored.
    """
    if handler_name not in log_config["root"]["handlers"]:
        log_config["root"]["handlers"].append(handler_name)


def _add_formatter(log_config: dict[str, Any], format_name: str, format_: str):
    """
    Register a formatter definition in the logging configuration.

    Parameters
    ----------
    log_config : dict[str, Any]
        Logging configuration dictionary.
    format_name : str
        Formatter identifier.
    format_ : str
        Logging format string.

    Notes
    -----
    Existing formatter definitions are preserved.
    """
    if format_name not in log_config["formatters"]:
        log_config["formatters"][format_name] = {"format": format_}


def _create_log_config(config: Config) -> dict[str, Any]:
    """
    Build the effective logging configuration.

    Creates a logging configuration dictionary by combining default
    logging settings with user-provided configuration options.

    Supported output targets include rotating log files, syslog and
    journald handlers.

    Parameters
    ----------
    config : Config
        Application configuration.

    Returns
    -------
    dict[str, Any]
        Logging configuration compatible with
        ``logging.config.dictConfig``.

    Raises
    ------
    OperationalException
        If required logging dependencies are unavailable or log file
        directories cannot be created.

    Notes
    -----
    Handler definitions may be modified dynamically depending on the
    current runtime environment.
    """
    # Get log_config from user config or use default
    log_config = config.get("log_config", deepcopy(FT_LOGGING_CONFIG))

    if logfile := config.get("logfile"):
        s = logfile.split(":")
        if s[0] == "syslog":
            logger.warning(
                "DEPRECATED: Configuring syslog logging via command line is deprecated."
                "Please use the log_config option in the configuration file instead."
            )
            # Add syslog handler to the config
            log_config["handlers"]["syslog"] = {
                "class": "logging.handlers.SysLogHandler",
                "formatter": "syslog_format",
                "address": (s[1], int(s[2])) if len(s) > 2 else s[1] if len(s) > 1 else "/dev/log",
            }

            _add_formatter(log_config, "syslog_format", "%(name)s - %(levelname)s - %(message)s")
            _add_root_handler(log_config, "syslog")

        elif s[0] == "journald":  # pragma: no cover
            # Check if we have the module available
            logger.warning(
                "DEPRECATED: Configuring Journald logging via command line is deprecated."
                "Please use the log_config option in the configuration file instead."
            )
            try:
                from cysystemd.journal import JournaldLogHandler  # noqa: F401
            except ImportError:
                raise OperationalException(
                    "You need the cysystemd python package be installed in order to use logging to journald."
                )

            # Add journald handler to the config
            log_config["handlers"]["journald"] = {
                "class": "cysystemd.journal.JournaldLogHandler",
                "formatter": "journald_format",
            }

            _add_formatter(log_config, "journald_format", "%(name)s - %(levelname)s - %(message)s")
            _add_root_handler(log_config, "journald")

        else:
            # Regular file logging
            # Update existing file handler configuration
            if "file" in log_config["handlers"]:
                log_config["handlers"]["file"]["filename"] = logfile
            else:
                log_config["handlers"]["file"] = {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "standard",
                    "filename": logfile,
                    "maxBytes": 1024 * 1024 * 10,  # 10Mb
                    "backupCount": 10,
                }
            _add_root_handler(log_config, "file")

    # TODO: split configuration generation into smaller helper functions?

    # TODO: separate file, syslog and journald configuration logic

    # Dynamically update some handlers
    for handler_config in log_config.get("handlers", {}).values():
        if handler_config.get("class") == "pysatl_experiment.loggers.rich_handler.FtRichHandler":
            handler_config["console"] = error_console
        elif handler_config.get("class") == "logging.handlers.RotatingFileHandler":
            logfile_path = Path(handler_config["filename"])
            try:
                # Create parent for filehandler
                logfile_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise OperationalException(
                    f'Failed to create or access log file "{logfile_path.absolute()}". '
                    "Please make sure you have the write permission to the log file or its parent "
                    "directories. If you're running PySatl using docker, you see this error "
                    "message probably because you've logged in as the root user, please switch to "
                    "non-root user, delete and recreate the directories you need, and then try "
                    "again."
                )
    return log_config


def setup_logging(config: Config) -> None:
    """
    Perform complete logging initialization.

    Applies logging configuration, registers required handlers,
    configures verbosity levels and enables optional colorized output.

    Parameters
    ----------
    config : Config
        Application configuration.

    Notes
    -----
    This function should be executed after application configuration
    has been fully loaded.

    Logging initialization may be skipped during test execution unless
    explicitly requested through configuration.
    """
    verbosity = config["verbosity"]
    if os.environ.get("PYTEST_VERSION") is None or config.get("tests_force_logging"):
        log_config = _create_log_config(config)
        _set_log_levels(log_config, verbosity, config.get("api_server", {}).get("verbosity", "info"))

        logging.config.dictConfig(log_config)

    # Add buffer handler to root logger
    if bufferHandler not in logging.root.handlers:
        logging.root.addHandler(bufferHandler)

    # Set color system for console output
    if config.get("print_colorized", True):
        logger.info("Enabling colorized output.")
        error_console._color_system = error_console._detect_color_system()  # TODO: fix protected member!!!!!!!

    logging.info("Logfile configured")

    # Set verbosity levels
    logging.root.setLevel(logging.INFO if verbosity < 1 else logging.DEBUG)

    logger.info("Verbosity set to %s", verbosity)

    # TODO: test -v/--verbose, --logfile options


#  TODO:
#       Separate configuration loading, handler registration and
#       verbosity management into dedicated components.

# TODO:
#       Extracting logging configuration construction into a
#       dedicated builder class

# TODO:
#       Global handler instances introduce shared mutable state.
#       Replace them with factory-created instances.
