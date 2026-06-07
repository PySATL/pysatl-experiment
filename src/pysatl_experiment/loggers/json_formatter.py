"""
JSON logging formatter implementation.

This module provides a logging formatter that serializes log records
into JSON objects. The formatter converts selected ``LogRecord``
attributes into a dictionary representation and serializes the result
using the standard JSON encoder.

The formatter is intended for machine-readable logging targets such as
log aggregation systems, centralized monitoring platforms and structured
logging pipelines.

The set of exported log record attributes is configurable through a
mapping between JSON field names and ``LogRecord`` attributes.
"""

import json
import logging


# TODO: replace loosely typed dictionaries with a dedicated TypedDict schema for formatter configuration?


class JsonFormatter(logging.Formatter):
    """
    Structured JSON formatter for Python logging.

    This formatter converts log records into dictionaries and serializes
    them as JSON strings. Individual output fields can be customized
    through a mapping between JSON keys and ``LogRecord`` attributes.

    Parameters
    ----------
    fmt_dict : dict[str, str] | None, default=None
        Mapping between output JSON field names and ``LogRecord``
        attribute names.

        If omitted, a default schema containing timestamp, level,
        logger name and message is used.

    time_format : str, default="%Y-%m-%dT%H:%M:%S"
        Timestamp format used when formatting log timestamps.

    msec_format : str, default="%s.%03dZ"
        Millisecond formatting template appended to formatted
        timestamps.

    Notes
    -----
        The formatter follows the standard ``logging.Formatter`` lifecycle
        and integrates with Python's logging infrastructure.
    """

    def __init__(
        self,
        fmt_dict: dict | None = None,
        time_format: str = "%Y-%m-%dT%H:%M:%S",
        msec_format: str = "%s.%03dZ",
    ):
        """
        Initialize the JSON formatter.

        Parameters
        ----------
        fmt_dict : dict | None, default=None
            Mapping between JSON field names and ``LogRecord`` attributes.

        time_format : str, default="%Y-%m-%dT%H:%M:%S"
            Format string used when rendering timestamps.

        msec_format : str, default="%s.%03dZ"
            Format string used for millisecond formatting.
        """
        super().__init__(fmt=None, datefmt=time_format)

        self.fmt_dict = (
            fmt_dict
            if fmt_dict is not None
            else {
                "timestamp": "asctime",
                "level": "levelname",
                "logger": "name",
                "message": "message",
            }
        )

        self.default_time_format = time_format
        self.default_msec_format = msec_format
        self.datefmt = None

    def usesTime(self) -> bool:
        """
        Determine whether timestamp generation is required.

        Returns
        -------
        bool
            ``True`` if at least one configured output field references
            the ``asctime`` attribute, otherwise ``False``.

        Notes
        -----
        This method overrides the default implementation from
        ``logging.Formatter``.

        The decision is based on formatter field mappings rather than a
        format string.
        """
        return "asctime" in self.fmt_dict.values()

    def formatMessage(self, record) -> str:
        """
        Disable string-based message formatting.

        Parameters
        ----------
        record : logging.LogRecord
            Log record being formatted.

        Returns
        -------
        str
            This method never returns successfully.

        Raises
        ------
        NotImplementedError
            Always raised because JSON formatting relies on dictionary
            serialization instead of string-based message formatting.

        Notes
        -----
        The standard ``logging.Formatter`` interface requires this method,
        but it is intentionally not used by this implementation.
        """
        raise NotImplementedError()

    def format_message_dict(self, record) -> dict:
        """
        Build a dictionary representation of a log record.

        Extracts configured attributes from the supplied ``LogRecord`` and
        returns them as a dictionary suitable for JSON serialization.

        Parameters
        ----------
        record : logging.LogRecord
            Log record being formatted.

        Returns
        -------
        dict
            Dictionary containing configured log fields.

        Raises
        ------
        KeyError
            Raised when a configured attribute does not exist on the
            supplied log record.

        Notes
        -----
        Field names in the returned dictionary correspond to keys defined
        in ``fmt_dict``.
        """
        return {fmt_key: record.__dict__[fmt_val] for fmt_key, fmt_val in self.fmt_dict.items()}

    def format(self, record) -> str:
        """
        Format a log record as a JSON string.

        Converts the supplied log record into a dictionary representation,
        enriches it with timestamp and exception information when
        applicable, and serializes the result as JSON.

        Parameters
        ----------
        record : logging.LogRecord
            Log record being formatted.

        Returns
        -------
        str
            JSON representation of the log record.

        Notes
        -----
        Exception tracebacks and stack traces are automatically included
        when available.

        The resulting JSON string is generated using ``json.dumps`` with
        ``default=str`` to support non-serializable values.
        """
        record.message = record.getMessage()

        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        message_dict = self.format_message_dict(record)

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            message_dict["exc_info"] = record.exc_text

        if record.stack_info:
            message_dict["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(message_dict, default=str)
