"""
Custom buffering log handler implementation.

This module provides a specialized buffering handler used by the
PySatl logging subsystem.

The handler is primarily used for in-memory log storage exposed through
application monitoring and debugging interfaces.
"""

from logging.handlers import BufferingHandler


class FTBufferingHandler(BufferingHandler):
    """
    Buffering handler that retains recent log records.

    This handler extends the standard Python buffering handler and
    modifies the flush behaviour to preserve a portion of recently
    collected log records.

    Notes
    -----
    The handler intentionally preserves recent log records during
    flush operations. This avoids situations where log consumers
    temporarily observe an empty buffer immediately after a flush.
    """

    def flush(self):
        """
        Flush the internal log buffer while retaining recent records.

        Instead of removing all buffered records, this implementation keeps
        some of the configured capacity and discards older entries.

        This approach ensures that a meaningful amount of recent logging
        information remains available after a flush operation.

        Notes
        -----
        The retained portion is currently fixed at 50% of the configured
        capacity.

        The operation is protected by the handler lock inherited from
        the standard logging infrastructure.
        """
        self.acquire()
        try:
            # Keep half of the records in buffer.
            records_to_keep = -int(self.capacity / 2)
            self.buffer = self.buffer[records_to_keep:]  # TODO: replace with queue/circular buffer??
        finally:
            self.release()
