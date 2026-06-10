"""
Rich-based logging handler for colorized console output.

This handler is designed for human-readable console logging using
the Rich library. It prioritizes visual clarity over structured or
machine-readable log formats.

It integrates with Python logging system but bypasses standard
formatting pipelines by constructing Rich Text output manually.

Notes
-----
This handler is intended for development and CLI usage only.

It is not suitable as a primary handler for structured logging,
file-based logging, or log aggregation systems.
"""

from datetime import datetime
from logging import Handler

from rich._null_file import NullFile
from rich.console import Console
from rich.text import Text


class FtRichHandler(Handler):
    """
    Custom Rich-based logging handler for colorized console output.

    This handler formats log records into a structured, colorized line
    using Rich Text components.

    Parameters
    ----------
    console : Console
        Rich console instance used for rendering output.

    Notes
    -----
    The handler directly constructs output format and does not rely on
    standard logging formatters.
    """

    def __init__(self, console: Console, *args, **kwargs) -> None:
        """
        Initialize Rich logging handler.

        Parameters
        ----------
        console : Console
            Rich console used for output rendering.

        Notes
        -----
        The console instance is stored internally and used during emit.
        """
        super().__init__(*args, **kwargs)
        self._console = console  # TODO: validate console instance type explicitly for robustness?

    def emit(self, record):
        """
        Render a log record using Rich and output it to the console.

        The method constructs a styled Rich Text object and prints it
        to the configured console.

        Parameters
        ----------
        record : logging.LogRecord
            The log record to be processed.

        Notes
        -----
        This method bypasses the standard logging formatting pipeline.

        Exceptions are passed to ``handleError`` as required by the logging
        framework.

        Special handling is applied for environments where stdout/stderr
        is unavailable (NullFile).
        """
        try:
            msg = self.format(record)
            # Format log message
            log_time = Text(
                datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S,%f")[:-3],
            )
            name = Text(record.name, style="violet")
            log_level = Text(record.levelname, style=f"logging.level.{record.levelname.lower()}")
            gray_sep = Text(" - ", style="gray46")

            if isinstance(self._console.file, NullFile):  # TODO: fix protected member!!!
                # Handles pythonw, where stdout/stderr are null, and we return NullFile
                # instance from Console.file. In this case, we still want to make a log record
                # even though we won't be writing anything to a file.
                self.handleError(record)
                return

            self._console.print(Text() + log_time + gray_sep + name + gray_sep + log_level + gray_sep + msg)

        except RecursionError:
            raise
        except Exception:
            self.handleError(record)  # TODO: fix warning!!


# TODO: replace hardcoded manual text composition with Rich's built-in logging renderers?
