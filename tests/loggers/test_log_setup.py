"""Tests for logging configuration and setup."""

from copy import deepcopy
from unittest.mock import patch

from pysatl_experiment.loggers import LOGGING_CONFIG, setup_logging


def test_setup_logging_uses_default_config():
    config = {}

    with patch("logging.config.dictConfig") as dict_config:
        setup_logging(config)

    dict_config.assert_called_once_with(LOGGING_CONFIG)


def test_setup_logging_uses_config_log_config():
    custom_config = {
        "version": 1,
        "handlers": {},
        "root": {},
    }

    config = {
        "log_config": custom_config,
    }

    with patch("logging.config.dictConfig") as dict_config:
        setup_logging(config)

    dict_config.assert_called_once_with(custom_config)


def test_setup_logging_adds_file_handler():
    config = {}

    with patch("logging.config.dictConfig") as dict_config:
        setup_logging(config, filename="test.log")

    passed_config = dict_config.call_args.args[0]

    assert "file" in passed_config["handlers"]

    file_handler = passed_config["handlers"]["file"]

    assert file_handler["class"] == "logging.handlers.RotatingFileHandler"
    assert file_handler["filename"] == "test.log"

    assert "file" in passed_config["root"]["handlers"]


def test_setup_logging_sets_handler_levels():
    config = {}

    with patch("logging.config.dictConfig") as dict_config:
        setup_logging(config, level="WARNING")

    passed_config = dict_config.call_args.args[0]

    for handler in passed_config["handlers"].values():
        assert handler["level"] == "WARNING"


def test_setup_logging_sets_level_for_console_and_file_handlers():
    config = {}

    with patch("logging.config.dictConfig") as dict_config:
        setup_logging(
            config,
            level="ERROR",
            filename="test.log",
        )

    passed_config = dict_config.call_args.args[0]

    assert passed_config["handlers"]["console"]["level"] == "ERROR"
    assert passed_config["handlers"]["file"]["level"] == "ERROR"


def test_setup_logging_does_not_mutate_global_logging_config():
    original = deepcopy(LOGGING_CONFIG)

    with patch("logging.config.dictConfig"):
        setup_logging({}, filename="test.log")

    assert LOGGING_CONFIG == original
    assert "file" not in LOGGING_CONFIG["handlers"]
