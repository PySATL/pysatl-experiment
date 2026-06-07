"""
Logging verbosity control utilities.

This module provides helper functions for dynamically adjusting logging
verbosity for specific subsystems at runtime.

The module targets specific logger namespaces and modifies their
logging levels via the standard Python logging system.

Notes
-----
This is a runtime side effect module that modifies global logging state.
"""

import logging


logger = logging.getLogger(__name__)


__BIAS_TESTER_LOGGERS = [
    "src.pysatl_experiment.resolvers",
]  # TODO: replace hardcoded global logger name list with a configuration-driven approach?


def reduce_verbosity_for_bias_tester() -> None:
    """
    Reduce logging verbosity for bias testing workflows.

    This function lowers the logging level for selected internal
    modules that tend to produce excessive log output during repeated
    execution of the same strategies.

    The goal is to improve log readability and reduce noise during
    batch experiments.

    Notes
    -----
    This function modifies global logging configuration at runtime.

    Affected loggers are defined in a module-level constant.
    """
    logger.info("Reducing verbosity for bias tester.")
    for logger_name in __BIAS_TESTER_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def restore_verbosity_for_bias_tester() -> None:
    """
    Restore default logging verbosity for bias testing components.

    This function resets logging levels for previously modified loggers
    back to their default verbosity level.

    It is intended to be used after completion of bias testing or
    batch execution workflows.

    Notes
    -----
    This function performs global side effects on the logging system.

    It should always be paired with
    ``reduce_verbosity_for_bias_tester``.
    """
    logger.info("Restoring log verbosity.")
    log_level = logging.NOTSET  # TODO: store previous log levels instead of using universal reset value?
    for logger_name in __BIAS_TESTER_LOGGERS:
        logging.getLogger(logger_name).setLevel(log_level)


# TODO: test nested levels for bugs
