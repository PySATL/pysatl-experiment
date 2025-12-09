import functools
import time
import pytest

from pysatl_experiment.parallel.scheduler import AdaptiveScheduler


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


class TestAdaptiveScheduler:

    def test_successful_task_execution(self):
        with AdaptiveScheduler(max_workers=2) as scheduler:
            results = scheduler.run([_test_task_simple, _test_task_simple])
        assert results == [42, 42]

    def test_exception_in_task(self):
        tasks = [_test_success_task, _test_failing_task]
        with pytest.raises(ValueError, match="Task failed"):
            with AdaptiveScheduler(max_workers=2) as scheduler:
                scheduler.run(tasks)

    def test_empty_task_list(self):
        with AdaptiveScheduler() as scheduler:
            results = scheduler.run([])
        assert results == []

    def test_task_with_arguments(self):
        tasks = [
            functools.partial(_test_task_with_args, 1, y=2),
            functools.partial(_test_task_with_args, 3)
        ]
        with AdaptiveScheduler(max_workers=2) as scheduler:
            results = scheduler.run(tasks)
        assert set(results) == {3, 13}

    def test_large_number_of_tasks(self):
        tasks = [functools.partial(_test_quick_task, i) for i in range(50)]
        with AdaptiveScheduler(max_workers=4) as scheduler:
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
        with AdaptiveScheduler(max_workers=3) as scheduler:
            for result in scheduler.iterate_results(tasks):
                results.append(result)
        assert len(results) == 3
        assert set(results) == {0.1, 0.3, 0.05}

    def test_context_manager_safety(self):
        scheduler = AdaptiveScheduler(max_workers=2)
        assert not scheduler._active
        with scheduler:
            assert scheduler._active
            results = scheduler.run([_test_task_simple, _test_task_simple])
        assert not scheduler._active
        assert results == [42, 42]

    def test_worker_adjustment(self, monkeypatch):
        cpu_values = iter([0.9, 0.2])
        monkeypatch.setattr("psutil.cpu_percent", lambda **kw: next(cpu_values))

        scheduler = AdaptiveScheduler(max_workers=4)
        scheduler._current_workers = 2

        scheduler._adjust_workers()
        assert scheduler._current_workers == 3

        scheduler._adjust_workers()
        assert scheduler._current_workers == 2

    def test_work_stealing_basic(self):
        tasks = [functools.partial(_test_simple_task, i) for i in range(5)]

        with AdaptiveScheduler(max_workers=2) as scheduler:
            results = list(scheduler.iterate_results(tasks))

        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}
