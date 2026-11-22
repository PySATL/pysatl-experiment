"""
Multiprocessing logging support.

Worker processes spawned by ``ProcessPoolExecutor`` do not inherit the
parent's logging configuration: module-level loggers exist, but no
handlers are attached, so worker records would be lost (or duplicated on
worker stderr, which is not captured).

This module implements the classic ``QueueHandler``/``QueueListener``
pair:

- In the parent process, ``WorkerLogListener`` owns a
  ``multiprocessing.Queue`` and a ``QueueListener`` that re-emits every
  incoming record through the parent's already-configured handlers
  (rich console and/or JSON file).
- In each worker process, ``configure_worker_logging`` replaces the
  root handlers with a single ``QueueHandler`` pointing at that queue.

Every record produced in a worker is automatically stamped with a
``worker_id`` attribute (the worker's PID), so JSON log consumers can
attribute records to a concrete process.
"""

import logging
import multiprocessing as mp
import os
from logging.handlers import QueueHandler, QueueListener
from multiprocessing.context import BaseContext
from multiprocessing.queues import Queue as MpQueue


class _WorkerIdFilter(logging.Filter):
    """Stamp records with the current PID as ``worker_id`` (unless set explicitly)."""

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add ``worker_id`` to the record if absent.

        Parameters
        ----------
        record : logging.LogRecord
            Log record being processed.

        Returns
        -------
        bool
            Always ``True`` — the filter enriches, never drops.
        """
        if not hasattr(record, "worker_id"):
            record.worker_id = os.getpid()
        return True


def configure_worker_logging(queue: "MpQueue[logging.LogRecord]", level: int) -> None:
    """
    Configure logging inside a worker process.

    Replaces all root handlers with a single ``QueueHandler`` that
    forwards records to the parent process listener, and applies the
    parent's root level so verbose records (e.g. ``--log-level DEBUG``)
    are not dropped in workers.

    Intended to be used as a ``ProcessPoolExecutor`` initializer, e.g.
    through ``Scheduler(worker_initializer=..., worker_initargs=...)``.

    Parameters
    ----------
    queue : multiprocessing.Queue
        Queue shared with the parent-side ``QueueListener``.
    level : int
        Root logger level to apply inside the worker (typically the
        parent's effective root level).
    """
    handler = QueueHandler(queue)
    handler.addFilter(_WorkerIdFilter())

    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)


class WorkerLogListener:
    """
    Parent-side listener forwarding worker log records to the configured handlers.

    Owns a ``multiprocessing.Queue`` shared with worker processes and a
    ``QueueListener`` that dispatches incoming records to the handlers
    attached to the root logger at start time (i.e. the ones installed
    by ``setup_logging()``). Records are emitted in the parent process,
    so handlers stay single-process and thread-safe by construction.

    Notes
    -----
    Use as a context manager and pass ``queue``/``level`` to the worker
    initializer::

        with WorkerLogListener() as log_ctx:
            with Scheduler(
                max_workers=n,
                worker_initializer=configure_worker_logging,
                worker_initargs=(log_ctx.queue, log_ctx.level),
            ) as scheduler:
                ...

    Parameters
    ----------
    mp_context : multiprocessing.context.BaseContext | None, optional
        Multiprocessing context used to create the queue. Must match the
        context of the ``ProcessPoolExecutor`` consuming it — a queue
        created in one context cannot be shared with processes started
        in another (e.g. fork queue + spawn executor fails at runtime).
        Defaults to the platform default context.
    """

    def __init__(self, mp_context: BaseContext | None = None) -> None:
        """
        Initialize the listener (no resources are allocated until start).

        Parameters
        ----------
        mp_context : multiprocessing.context.BaseContext | None, optional
            Multiprocessing context for the queue; defaults to the
            platform default context.
        """
        self._mp_context = mp_context or mp.get_context()
        self._queue: MpQueue[logging.LogRecord] | None = None
        self._listener: QueueListener | None = None
        self.level: int = logging.WARNING

    @property
    def queue(self) -> "MpQueue[logging.LogRecord]":
        """
        Queue shared with worker processes.

        Returns
        -------
        multiprocessing.Queue
            Queue to pass to ``configure_worker_logging`` in workers.

        Raises
        ------
        RuntimeError
            If accessed outside of the ``with`` block.
        """
        if self._queue is None:
            raise RuntimeError("WorkerLogListener is not started. Use 'with WorkerLogListener() as ctx:'.")
        return self._queue

    def __enter__(self) -> "WorkerLogListener":
        """
        Start the listener and snapshot the current root handlers.

        Returns
        -------
        WorkerLogListener
            The started listener context.
        """
        root = logging.getLogger()
        self.level = root.getEffectiveLevel()
        self._queue = self._mp_context.Queue()
        self._listener = QueueListener(self._queue, *root.handlers[:], respect_handler_level=True)
        self._listener.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Stop the listener, flushing pending worker records.

        Parameters
        ----------
        exc_type : type | None
            Exception type.
        exc_val : BaseException | None
            Exception value.
        exc_tb : object | None
            Exception traceback.
        """
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self._queue = None
