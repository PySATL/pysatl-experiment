"""Tests for multiprocessing logging (QueueHandler/QueueListener pair).

Three layers, mirroring the rest of the logging test suite:

- unit shape: ``configure_worker_logging`` installs a QueueHandler and
  stamps ``worker_id``;
- behavior: ``WorkerLogListener`` forwards records from the queue to the
  parent handlers;
- integration: a real ``ProcessPoolExecutor`` (spawn context) worker's
  log records arrive at the parent's handlers via ``Scheduler``.
"""

import logging
import multiprocessing as mp
import os
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from logging.handlers import QueueHandler
from multiprocessing.queues import Queue as MpQueue

import pytest

from pysatl_experiment.experiment_execution.parallel import Scheduler
from pysatl_experiment.loggers.multiprocessing import WorkerLogListener, configure_worker_logging


class _ListHandler(logging.Handler):
    """Test handler collecting emitted records in a list."""

    def __init__(self, records: list[logging.LogRecord]) -> None:
        super().__init__(level=logging.DEBUG)
        self.records = records

    def emit(self, record: logging.LogRecord) -> None:
        """Collect the record."""
        self.records.append(record)


def _log_from_worker(index: int) -> int:
    """Emit one INFO record from a worker process (module-level for pickling)."""
    logging.getLogger("pysatl_experiment.mp_probe").info("worker message %d", index)
    return index


@pytest.mark.usefixtures("preserve_logging_state")
def test_configure_worker_logging_installs_queue_handler() -> None:
    """Worker setup must replace root handlers with a single QueueHandler at the given level."""
    log_queue: MpQueue[logging.LogRecord] = mp.Queue()

    configure_worker_logging(log_queue, logging.DEBUG)

    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0], QueueHandler)
    assert root.level == logging.DEBUG

    logging.getLogger("pysatl_experiment.worker_shape_probe").info("shape probe")
    record = log_queue.get(timeout=5)
    assert record.getMessage() == "shape probe"
    assert record.worker_id == os.getpid()  # type: ignore[attr-defined]


@pytest.mark.usefixtures("preserve_logging_state")
def test_configure_worker_logging_keeps_explicit_worker_id() -> None:
    """A caller-supplied ``worker_id`` (e.g. a logical index) must not be overwritten."""
    log_queue: MpQueue[logging.LogRecord] = mp.Queue()

    configure_worker_logging(log_queue, logging.INFO)

    logging.getLogger("pysatl_experiment.worker_id_probe").info("id probe", extra={"worker_id": "w7"})
    record = log_queue.get(timeout=5)
    assert record.worker_id == "w7"  # type: ignore[attr-defined]


@pytest.mark.usefixtures("preserve_logging_state")
def test_worker_log_listener_forwards_records_to_parent_handlers() -> None:
    """Records put on the queue must be re-emitted through the parent's root handlers."""
    records: list[logging.LogRecord] = []
    logging.getLogger().addHandler(_ListHandler(records))

    with WorkerLogListener() as log_ctx:
        assert log_ctx.level == logging.getLogger().getEffectiveLevel()
        log_ctx.queue.put(logging.makeLogRecord({"msg": "queued probe", "levelno": logging.INFO}))

    assert any(r.getMessage() == "queued probe" for r in records)


@pytest.mark.usefixtures("preserve_logging_state")
def test_listener_queue_access_outside_context_raises() -> None:
    """The queue must not be exposed before start / after stop."""
    listener = WorkerLogListener()
    with pytest.raises(RuntimeError, match="not started"):
        _ = listener.queue


@pytest.mark.usefixtures("preserve_logging_state")
def test_spawned_worker_records_reach_parent_handlers() -> None:
    """End-to-end: records from a spawned worker process land in parent handlers."""
    records: list[logging.LogRecord] = []
    root = logging.getLogger()
    root.addHandler(_ListHandler(records))
    root.setLevel(logging.INFO)

    ctx = mp.get_context("spawn")
    with WorkerLogListener() as log_ctx:
        with ProcessPoolExecutor(
            max_workers=1,
            mp_context=ctx,
            initializer=configure_worker_logging,
            initargs=(log_ctx.queue, log_ctx.level),
        ) as executor:
            assert list(executor.map(_log_from_worker, range(2))) == [0, 1]

    messages = [r.getMessage() for r in records]
    assert "worker message 0" in messages
    assert "worker message 1" in messages
    worker_records = [r for r in records if r.name == "pysatl_experiment.mp_probe"]
    assert all(r.worker_id != os.getpid() for r in worker_records)  # type: ignore[attr-defined]


@pytest.mark.usefixtures("preserve_logging_state")
def test_scheduler_runs_worker_initializer() -> None:
    """Scheduler must plumb the logging initializer through to its workers."""
    records: list[logging.LogRecord] = []
    root = logging.getLogger()
    root.addHandler(_ListHandler(records))
    root.setLevel(logging.INFO)

    with WorkerLogListener() as log_ctx:
        with Scheduler(
            max_workers=1,
            worker_initializer=configure_worker_logging,
            worker_initargs=(log_ctx.queue, log_ctx.level),
        ) as scheduler:
            assert scheduler.run([partial(_log_from_worker, 0)]) == [0]

    assert any(r.getMessage() == "worker message 0" for r in records)
