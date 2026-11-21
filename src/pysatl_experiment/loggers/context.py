"""
Contextual logging adapter for experiment runs.

This module provides a ``logging.LoggerAdapter`` that attaches experiment
context (experiment id, pipeline step) to every emitted log record.

The context is exposed in two ways:

1. As a compact prefix in the rendered message, so it is visible in
   human-readable console output regardless of the formatter in use.
2. As structured ``extra`` fields on the ``LogRecord``, so JSON-formatted
   destinations (e.g. log files consumed by aggregation pipelines) receive
   the context as dedicated machine-readable fields.
"""

import logging
from collections.abc import MutableMapping
from typing import Any


class ExperimentContextAdapter(logging.LoggerAdapter):
    """
    Logger adapter that injects experiment context into log records.

    Parameters
    ----------
    logger : logging.Logger
        Underlying logger instance.
    extra : dict[str, Any]
        Base context merged into every record. Typically contains
        ``experiment_id``. Per-call context (e.g. ``step``) can be added
        through the standard ``extra`` keyword argument of logging calls.

    Notes
    -----
    The adapter prepends a ``[key=value, ...]`` prefix built from the
    merged context to the message and passes the context through as
    record attributes via the ``extra`` mechanism.

    The merged context is also stored on the record, so structured
    formatters (such as ``JsonFormatter`` with ``include_extra=True``)
    export it as dedicated fields.
    """

    def process(self, msg: Any, kwargs: MutableMapping[str, Any]) -> tuple[Any, MutableMapping[str, Any]]:
        """
        Merge adapter and per-call context into the log record.

        Parameters
        ----------
        msg : Any
            Log message.
        kwargs : MutableMapping[str, Any]
            Keyword arguments passed to the logging call.

        Returns
        -------
        tuple[Any, MutableMapping[str, Any]]
            Message with the context prefix and keyword arguments with
            the merged ``extra`` mapping.
        """
        merged: dict[str, Any] = {**(self.extra or {}), **(kwargs.get("extra") or {})}
        kwargs["extra"] = merged

        if merged:
            prefix = ", ".join(f"{key}={value}" for key, value in merged.items())
            msg = f"[{prefix}] {msg}"

        return msg, kwargs
