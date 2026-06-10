"""
Standard error stream logging handler.

This module implements a custom logging handler that writes formatted
log records directly to ``sys.stderr``.

It is primarily used to ensure immediate visibility of log output in
environments where standard logging handlers may be buffered or
redirected.

The handler provides explicit control over flushing behavior to reduce
log delay in interactive and real-time execution environments.

Notes
-----
This handler bypasses ``logging.StreamHandler`` buffering behavior and
writes directly to stderr.
"""

import sys
from logging import Handler


class FTStdErrStreamHandler(Handler):
    """
    Logging handler that writes directly to standard error stream.

    This handler provides low-level stderr output for log records,
    bypassing higher-level stream abstractions.

    It is designed for environments where immediate log visibility is
    required.

    Notes
    -----
    This handler duplicates functionality partially provided by
    ``logging.StreamHandler``.
    """

    def flush(self):
        """
        Flush stderr output stream.

        This method ensures that all buffered stderr output is written
        immediately.

        Behavior
        --------
        The flush operation is protected by the handler lock to ensure
        thread safety.

        Notes
        -----
        Unlike standard stream handlers, this implementation explicitly
        flushes ``sys.stderr`` on every call.
        """
        self.acquire()
        try:
            sys.stderr.flush()
        finally:
            self.release()

    def emit(self, record):
        """
        Emit a log record to standard error output.

        The record is formatted using the handler's formatter and written
        directly to ``sys.stderr``.

        Behavior
        --------
        Each log record is immediately flushed to ensure real-time output.

        Error handling follows the standard logging pattern using
        ``handleError``.

        Notes
        -----
        This implementation bypasses buffering mechanisms and may impact
        performance under heavy logging load.
        """
        try:
            msg = self.format(record)
            # Don't keep a reference to stderr - this can be problematic with progressbars.
            sys.stderr.write(msg + "\n")
            self.flush()
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)  # TODO: fix warning!!


# TODO: is this handler needed at all instead of StreamHandler? if so, check for tests
