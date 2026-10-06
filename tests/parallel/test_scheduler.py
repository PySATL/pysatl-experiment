"""Tests for task scheduler."""

import functools
import time
from collections.abc import Sequence
from concurrent.futures import Future
from typing import Any, ClassVar

import pytest

from pysatl_experiment.experiment_execution.parallel import Scheduler
from pysatl_experiment.experiment_execution.parallel import scheduler as scheduler_module


def _test_task_simple():
    return 42


def _test_task_with_args(x, y=10):
    return x + y


def _test_failing_task():
    raise ValueError("Task failed")


def _test_success_task():
    return "ok"


def _test_quick_task(i):
    return i * 2


def _test_variable_task(duration):
    time.sleep(duration)
    return duration


def _test_slow_task(name, duration=0.1):
    time.sleep(duration)
    return name


def _test_simple_task(i):
    return i


class InlineExecutor:
    """Process pool stub that executes every submitted callable immediately."""

    instances: ClassVar[list["InlineExecutor"]] = []

    def __init__(self, max_workers: int | None = None) -> None:
        self.max_workers = max_workers
        self.submitted: list[tuple[Any, ...]] = []
        self.shutdown_calls: int = 0
        InlineExecutor.instances.append(self)

    def submit(self, fn, *args, **kwargs) -> Future:
        """Run ``fn`` synchronously and return an already resolved future."""
        self.submitted.append(args)
        future: Future = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except BaseException as exc:  # noqa: BLE001
            future.set_exception(exc)
        return future

    def shutdown(self, wait: bool = True) -> None:
        """Record that the scheduler stopped the executor."""
        self.shutdown_calls += 1


class TestAdaptiveScheduler:
    def test_successful_task_execution(self):
        with Scheduler(max_workers=2) as scheduler:
            results = scheduler.run([_test_task_simple, _test_task_simple])
        assert results == [42, 42]

    def test_exception_in_task(self):
        tasks = [_test_success_task, _test_failing_task]
        with pytest.raises(ValueError, match="Task failed"):
            with Scheduler(max_workers=2) as scheduler:
                scheduler.run(tasks)

    def test_empty_task_list(self):
        with Scheduler(max_workers=1) as scheduler:
            results = scheduler.run([])
        assert results == []

    def test_task_with_arguments(self):
        tasks = [functools.partial(_test_task_with_args, 1, y=2), functools.partial(_test_task_with_args, 3)]
        with Scheduler(max_workers=2) as scheduler:
            results = scheduler.run(tasks)
        assert set(results) == {3, 13}

    def test_large_number_of_tasks(self):
        tasks = [functools.partial(_test_quick_task, i) for i in range(50)]
        with Scheduler(max_workers=4) as scheduler:
            results = scheduler.run(tasks)
        assert len(results) == 50
        assert set(results) == {i * 2 for i in range(50)}

    def test_iterate_results_order_independence(self):
        tasks = [
            functools.partial(_test_variable_task, 0.1),
            functools.partial(_test_variable_task, 0.3),
            functools.partial(_test_variable_task, 0.05),
        ]
        results = []
        with Scheduler(max_workers=3) as scheduler:
            for result in scheduler.iterate_results(tasks):
                results.append(result)
        assert len(results) == 3
        assert set(results) == {0.1, 0.3, 0.05}

    def test_context_manager_safety(self):
        scheduler = Scheduler(max_workers=2)
        assert not scheduler._active
        with scheduler:
            assert scheduler._active
            results = scheduler.run([_test_task_simple, _test_task_simple])
        assert not scheduler._active
        assert results == [42, 42]

    def test_work_stealing_basic(self):
        tasks = [functools.partial(_test_simple_task, i) for i in range(5)]

        with Scheduler(max_workers=2) as scheduler:
            results = list(scheduler.iterate_results(tasks))

        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}


# Checks that starting an already running scheduler is rejected.
def test_start_twice_raises_runtime_error():
    scheduler = Scheduler(max_workers=2)
    scheduler.start()

    try:
        with pytest.raises(RuntimeError, match="Scheduler is already running."):
            scheduler.start()
    finally:
        scheduler.shutdown()


# Checks that submitting before the scheduler is started is rejected.
def test_submit_before_start_raises_runtime_error():
    scheduler = Scheduler(max_workers=2)

    with pytest.raises(RuntimeError, match="Scheduler is not started."):
        scheduler.submit(_test_task_simple)


# Checks that iterating results outside a context manager is rejected.
def test_iterate_results_outside_context_raises_runtime_error():
    scheduler = Scheduler(max_workers=2)

    with pytest.raises(RuntimeError, match="Use inside 'with' block."):
        list(scheduler.iterate_results([_test_task_simple]))


# Checks that running tasks outside a context manager is rejected.
def test_run_outside_context_raises_runtime_error():
    scheduler = Scheduler(max_workers=2)

    with pytest.raises(RuntimeError, match="Use inside 'with' block."):
        scheduler.run([_test_task_simple])


# Checks that shutting down a never started scheduler is safe.
def test_shutdown_without_start_is_safe():
    scheduler = Scheduler(max_workers=2)

    scheduler.shutdown()

    assert not scheduler._active


# Checks that a repeated shutdown does not raise.
def test_repeated_shutdown_is_safe():
    scheduler = Scheduler(max_workers=2)
    scheduler.start()
    scheduler.shutdown()

    scheduler.shutdown()

    assert not scheduler._active


# Checks that the scheduler can be restarted in a second context manager block.
def test_scheduler_can_be_restarted():
    scheduler = Scheduler(max_workers=2)

    with scheduler:
        first = scheduler.run([_test_task_simple])

    with scheduler:
        second = scheduler.run([_test_task_simple])

    assert first == second == [42]


# Checks that the worker count is forwarded to the executor factory.
def test_scheduler_forwards_max_workers(monkeypatch):
    created = []

    class RecordingExecutor:
        """Executor stub recording the configured worker count."""

        def __init__(self, max_workers=None):
            created.append(max_workers)

        def submit(self, fn, *args, **kwargs):
            raise NotImplementedError

        def shutdown(self, wait=True):
            pass

    monkeypatch.setattr(scheduler_module, "ProcessPoolExecutor", RecordingExecutor)

    scheduler = Scheduler(max_workers=7)
    scheduler.start()
    scheduler.shutdown()

    assert created == [7]


# Checks that a TimeoutError raised while collecting results is retried.
def test_timeout_error_is_retried(monkeypatch):
    real_as_completed = scheduler_module.as_completed
    calls = []

    def flaky_as_completed(futures, *args, **kwargs):
        """Raise TimeoutError once, then delegate to the real implementation."""
        calls.append(True)
        if len(calls) == 1:
            raise TimeoutError
        return real_as_completed(futures, *args, **kwargs)

    monkeypatch.setattr(scheduler_module, "as_completed", flaky_as_completed)

    with Scheduler(max_workers=2) as scheduler:
        results = scheduler.run([_test_task_simple, _test_success_task])

    assert sorted(results, key=str) == sorted([42, "ok"], key=str)
    assert len(calls) == 2


# Checks that the initial fill stops early when the sequence under-reports its items.
def test_initial_fill_stops_on_exhausted_iterator(monkeypatch):
    class UnderReportingSequence(Sequence):
        """Sequence whose reported length exceeds the number of yielded items."""

        def __init__(self, items) -> None:
            self._items = list(items)

        def __len__(self) -> int:
            return len(self._items) + 5

        def __getitem__(self, index):
            return self._items[index]

    monkeypatch.setattr(scheduler_module, "ProcessPoolExecutor", InlineExecutor)

    with Scheduler(max_workers=10) as scheduler:
        results = scheduler.run(UnderReportingSequence([_test_task_simple]))

    assert results == [42]


# Checks that submit forwards positional and keyword arguments to the executor.
def test_submit_forwards_arguments(monkeypatch):
    monkeypatch.setattr(scheduler_module, "ProcessPoolExecutor", InlineExecutor)

    with Scheduler(max_workers=2) as scheduler:
        future = scheduler.submit(_test_task_with_args, 1, y=2)

    assert future.result() == 3
