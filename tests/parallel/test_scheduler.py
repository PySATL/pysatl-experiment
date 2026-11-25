"""Tests for task scheduler."""

import functools
import time
from collections.abc import Sequence
from concurrent.futures import Future
from typing import Any, ClassVar

import pytest

from pysatl_experiment.configuration.models.task_failure_policy import TaskFailurePolicy
from pysatl_experiment.experiment_execution.parallel import Scheduler, TaskFailuresExceededError
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

    def __init__(self, max_workers: int | None = None, mp_context=None, initializer=None, initargs=()) -> None:
        self.max_workers = max_workers
        self.mp_context = mp_context
        self.initializer = initializer
        self.initargs = initargs
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

        def __init__(self, max_workers=None, mp_context=None, initializer=None, initargs=()):
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


# Checks that the worker initializer and its arguments are forwarded to the executor factory.
def test_scheduler_forwards_worker_initializer(monkeypatch):
    recorded = {}

    class RecordingExecutor:
        """Executor stub recording the initializer wiring."""

        def __init__(self, max_workers=None, mp_context=None, initializer=None, initargs=()):
            recorded["max_workers"] = max_workers
            recorded["mp_context"] = mp_context
            recorded["initializer"] = initializer
            recorded["initargs"] = initargs

        def submit(self, fn, *args, **kwargs):
            raise NotImplementedError

        def shutdown(self, wait=True):
            pass

    def _noop_initializer():
        pass

    monkeypatch.setattr(scheduler_module, "ProcessPoolExecutor", RecordingExecutor)

    scheduler = Scheduler(max_workers=3, worker_initializer=_noop_initializer, worker_initargs=("a", 1))
    scheduler.start()
    scheduler.shutdown()

    assert recorded == {
        "max_workers": 3,
        "mp_context": None,
        "initializer": _noop_initializer,
        "initargs": ("a", 1),
    }


# Checks that a task failure is isolated, recorded and does not stop the remaining tasks.
def test_isolate_policy_records_failure_and_continues(monkeypatch):
    monkeypatch.setattr(scheduler_module, "ProcessPoolExecutor", InlineExecutor)

    tasks = [_test_success_task, _test_failing_task, _test_task_simple]

    with Scheduler(max_workers=2) as scheduler:
        results = scheduler.run(tasks, failure_policy=TaskFailurePolicy.ISOLATE, failure_threshold=0.5)

    assert sorted(results, key=str) == sorted(["ok", 42], key=str)
    assert len(scheduler.failures) == 1
    assert scheduler.failures[0].index == 1
    assert isinstance(scheduler.failures[0].error, ValueError)


# Checks that new tasks are still submitted after a failure under the isolate policy.
def test_isolate_policy_keeps_submitting_after_failure(monkeypatch):
    monkeypatch.setattr(scheduler_module, "ProcessPoolExecutor", InlineExecutor)

    tasks = [_test_failing_task, _test_success_task, _test_success_task, _test_success_task]

    with Scheduler(max_workers=2) as scheduler:
        results = scheduler.run(tasks, failure_policy=TaskFailurePolicy.ISOLATE, failure_threshold=1.0)

    assert results == ["ok", "ok", "ok"]
    assert len(scheduler.failures) == 1


# Checks that the failure records are reset between iterate_results calls.
def test_failures_are_reset_between_runs(monkeypatch):
    monkeypatch.setattr(scheduler_module, "ProcessPoolExecutor", InlineExecutor)

    with Scheduler(max_workers=2) as scheduler:
        scheduler.run([_test_failing_task], failure_policy=TaskFailurePolicy.ISOLATE, failure_threshold=1.0)
        assert len(scheduler.failures) == 1

        scheduler.run([_test_success_task])
        assert scheduler.failures == []


# Checks that exceeding the failure threshold escalates to TaskFailuresExceededError after draining.
def test_isolate_policy_escalates_when_threshold_exceeded(monkeypatch):
    monkeypatch.setattr(scheduler_module, "ProcessPoolExecutor", InlineExecutor)

    tasks = [_test_failing_task, _test_failing_task, _test_success_task, _test_success_task]

    with Scheduler(max_workers=2) as scheduler:
        with pytest.raises(TaskFailuresExceededError, match="2 of 4 tasks failed"):
            scheduler.run(tasks, failure_policy=TaskFailurePolicy.ISOLATE, failure_threshold=0.25)

    assert len(scheduler.failures) == 2


# Checks that a failure share equal to the threshold does not escalate.
def test_isolate_policy_allows_failures_at_threshold(monkeypatch):
    monkeypatch.setattr(scheduler_module, "ProcessPoolExecutor", InlineExecutor)

    tasks = [_test_failing_task, _test_success_task, _test_success_task, _test_success_task]

    with Scheduler(max_workers=2) as scheduler:
        results = scheduler.run(tasks, failure_policy=TaskFailurePolicy.ISOLATE, failure_threshold=0.25)

    assert results == ["ok", "ok", "ok"]


# Checks that out-of-range failure thresholds are rejected.
@pytest.mark.parametrize("threshold", [-0.1, 1.1])
def test_invalid_failure_threshold_raises_value_error(threshold):
    scheduler = Scheduler(max_workers=2)

    with pytest.raises(ValueError, match="failure_threshold"):
        list(scheduler.iterate_results([_test_task_simple], failure_threshold=threshold))


# Checks that the fail-fast policy remains the default and re-raises task exceptions.
def test_fail_fast_policy_is_default():
    with pytest.raises(ValueError, match="Task failed"), Scheduler(max_workers=2) as scheduler:
        scheduler.run([_test_success_task, _test_failing_task])


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
