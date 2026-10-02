"""Universal tasks, bounded scheduling and context ownership in real pools."""

import os
from collections import defaultdict
from concurrent.futures import BrokenExecutor
from dataclasses import dataclass, field
from functools import partial
from multiprocessing import get_context
from threading import Barrier, Event, Lock, get_ident
from uuid import uuid4

import pytest

from pysatl_experiment.parallel import Scheduler, no_context


def add(value: int, context: None, *, increment: int = 1) -> int:
    return value + increment


def return_none(context: None) -> None:
    return None


def fail(context: None) -> None:
    raise TimeoutError("task timeout")


def failed_factory() -> None:
    raise RuntimeError("factory failed")


@dataclass(frozen=True)
class Multiply:
    value: int

    def __call__(self, context: None) -> int:
        return self.value * 2


@dataclass
class WorkerContext:
    barrier: object
    owner: tuple[int, int] = field(default_factory=lambda: (os.getpid(), get_ident()))
    token: str = field(default_factory=lambda: uuid4().hex)
    calls: int = 0
    # A context must stay in its worker: this lock cannot be pickled.
    lock: object = field(default_factory=Lock)


def make_context(barrier) -> WorkerContext:
    return WorkerContext(barrier)


def visit(context: WorkerContext):
    assert context.owner == (os.getpid(), get_ident())
    context.calls += 1
    context.barrier.wait(timeout=10)
    return context.owner, context.token, context.calls


def identify(context: WorkerContext):
    context.calls += 1
    return context.token, context.calls


@pytest.mark.parametrize("backend", ["thread", "process"])
def test_functions_callable_objects_and_none_results(backend):
    with Scheduler(2, no_context, backend=backend) as scheduler:
        assert sorted(scheduler.run(Multiply(i) for i in range(20))) == list(range(0, 40, 2))
        assert scheduler.submit(partial(add, 10, increment=5)).result() == 15
        assert scheduler.run([return_none]) == [None]
        assert scheduler.run(iter(())) == []


@pytest.mark.parametrize("backend", ["thread", "process"])
def test_context_is_created_in_each_worker_and_reused(backend):
    barrier = get_context("spawn").Barrier(2) if backend == "process" else Barrier(2)
    with Scheduler(2, partial(make_context, barrier), backend=backend) as scheduler:
        results = scheduler.run([visit] * 8)
    workers = defaultdict(list)
    for owner, token, count in results:
        workers[owner].append((token, count))
    assert len(workers) == 2
    for owner, calls in workers.items():
        assert len({token for token, _ in calls}) == 1
        assert sorted(count for _, count in calls) == [1, 2, 3, 4]
        assert owner != (os.getpid(), get_ident())
        if backend == "process":
            assert owner[0] != os.getpid()


@pytest.mark.parametrize("backend", ["thread", "process"])
def test_lifecycle_and_repeated_runs(backend):
    scheduler = Scheduler(1, partial(make_context, None), backend=backend)
    with pytest.raises(RuntimeError, match="not started"):
        scheduler.submit(identify)
    with pytest.raises(RuntimeError, match="not started"):
        scheduler.run([])
    with scheduler:
        with pytest.raises(RuntimeError, match="already running"):
            scheduler.start()
        token, count = scheduler.run([identify])[0]
        assert count == 1
        assert scheduler.run([identify]) == [(token, 2)]
    with pytest.raises(RuntimeError, match="not started"):
        scheduler.submit(identify)
    scheduler.shutdown()
    with scheduler:
        new_token, count = scheduler.run([identify])[0]
        assert new_token != token and count == 1


@pytest.mark.parametrize("backend", ["thread", "process"])
def test_task_timeout_is_propagated_and_input_is_not_consumed_after_failure(backend):
    def tasks():
        yield fail
        pytest.fail("The scheduler consumed input after a failed task")

    with Scheduler(1, no_context, backend=backend, max_pending=1) as scheduler:
        with pytest.raises(TimeoutError, match="task timeout"):
            scheduler.run(tasks())


@pytest.mark.parametrize("backend", ["thread", "process"])
def test_factory_failure_is_propagated(backend):
    with Scheduler(1, failed_factory, backend=backend) as scheduler:
        with pytest.raises(BrokenExecutor):
            scheduler.run([return_none])


def test_input_is_lazy_and_pending_work_is_bounded():
    produced = []

    def tasks():
        for i in range(100):
            produced.append(i)
            yield Multiply(i)

    with Scheduler(1, no_context, backend="thread", max_pending=2) as scheduler:
        results = scheduler.iterate_results(tasks())
        assert produced == []
        next(results)
        assert produced == [0, 1]
        next(results)
        assert produced == [0, 1, 2]
        results.close()
        assert produced == [0, 1, 2]


def test_fast_worker_keeps_receiving_tasks_while_another_is_busy():
    release = Event()

    def slow(context):
        assert release.wait(timeout=5), "Fast worker stopped refilling its queue"
        return "slow"

    def unblock(context):
        release.set()
        return "unblock"

    with Scheduler(2, no_context, backend="thread", max_pending=2) as scheduler:
        try:
            results = scheduler.run([slow, Multiply(1), Multiply(2), unblock])
            assert set(results) == {"slow", 2, 4, "unblock"}
        finally:
            release.set()


def test_closing_iterator_cancels_queued_tasks():
    release = Event()
    executed = []

    def blocked(context):
        assert release.wait(timeout=5)

    def queued(context):
        executed.append("queued")

    with Scheduler(1, no_context, backend="thread", max_pending=3) as scheduler:
        results = scheduler.iterate_results([Multiply(1), blocked, queued])
        try:
            assert next(results) == 2
            results.close()
        finally:
            release.set()
    assert executed == []


def test_input_failure_is_propagated():
    def tasks():
        yield Multiply(1)
        raise ValueError("input failed")

    with Scheduler(1, no_context, backend="thread") as scheduler:
        with pytest.raises(ValueError, match="input failed"):
            scheduler.run(tasks())


def test_concurrent_thread_pools_have_independent_contexts():
    with (
        Scheduler(1, partial(make_context, None), backend="thread") as first,
        Scheduler(1, partial(make_context, None), backend="thread") as second,
    ):
        one = first.submit(identify).result()
        two = second.submit(identify).result()
        assert one[0] != two[0]
        assert first.submit(identify).result() == (one[0], 2)
        assert second.submit(identify).result() == (two[0], 2)


@pytest.mark.parametrize("field_name", ["max_workers", "max_pending"])
@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_invalid_limits(field_name, value):
    kwargs = {"max_workers": 1, "context_factory": no_context, field_name: value}
    with pytest.raises(ValueError, match=field_name):
        Scheduler(**kwargs)


def test_invalid_backend():
    with pytest.raises(ValueError, match="backend"):
        Scheduler(1, no_context, backend="unknown")
