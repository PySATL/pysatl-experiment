"""Execution batches are bounded and retain completed work on task failure."""

from collections.abc import Iterator
from functools import partial
from unittest.mock import Mock

import pytest

from pysatl_experiment.experiment_execution.step.execution_step import parallel_execution_step
from pysatl_experiment.experiment_execution.step.execution_step.parallel_execution_step import ParallelExecutionStep
from pysatl_experiment.parallel import Scheduler, no_context
from pysatl_experiment.persistence.contracts.time_complexity import ITimeComplexityStorage
from pysatl_experiment.persistence.models.time_complexity import TimeComplexityModel


def execute_value(value: int, context: None) -> int:
    if value < 0:
        raise RuntimeError("Task failed")
    return value


class BatchingStep(ParallelExecutionStep[int, int, TimeComplexityModel, ITimeComplexityStorage, None]):
    def __init__(self, values, storage, write_batch_size=20):
        super().__init__(1, storage, no_context, total_tasks=len(values), write_batch_size=write_batch_size)
        self.values = values

    def _collect_tasks(self) -> Iterator[int]:
        yield from self.values

    def _make_task(self, spec: int):
        return partial(execute_value, spec)

    def _to_model(self, result: int) -> TimeComplexityModel:
        return TimeComplexityModel("experiment", "criterion", {}, 1, 1, [float(result)], "normal")

    def _bulk_save(self, models: list[TimeComplexityModel]) -> None:
        self.result_storage.bulk_insert(models, batch_size=self.write_batch_size)


@pytest.fixture
def serial_scheduler(monkeypatch):
    # One pending task makes failure ordering deterministic while using the real scheduler.
    monkeypatch.setattr(parallel_execution_step, "Scheduler", partial(Scheduler, backend="thread", max_pending=1))


@pytest.mark.parametrize(("count", "sizes"), [(0, []), (1, [1]), (4, [2, 2]), (5, [2, 2, 1])])
def test_lazy_tasks_save_full_batches_and_remainder(serial_scheduler, count, sizes):
    storage = Mock(spec=ITimeComplexityStorage)
    BatchingStep(range(count), storage, write_batch_size=2).run()
    batches = [call.args[0] for call in storage.bulk_insert.call_args_list]
    assert [len(batch) for batch in batches] == sizes
    assert [model.results_times[0] for batch in batches for model in batch] == list(range(count))


def test_failure_flushes_completed_results_and_propagates(serial_scheduler):
    storage = Mock(spec=ITimeComplexityStorage)
    step = BatchingStep([0, 1, 2, -1], storage, write_batch_size=2)
    with pytest.raises(RuntimeError, match="Task failed"):
        step.run()
    batches = [call.args[0] for call in storage.bulk_insert.call_args_list]
    assert [[model.results_times[0] for model in batch] for batch in batches] == [[0.0, 1.0], [2.0]]


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "2", None])
def test_invalid_write_batch_size_is_rejected(value):
    with pytest.raises(ValueError, match="write_batch_size"):
        BatchingStep([], Mock(), write_batch_size=value)


def test_progress_is_visible_before_work_and_success_waits_for_final_save(serial_scheduler, monkeypatch):
    from io import StringIO

    from rich.console import Console

    from pysatl_experiment.experiment_execution.step import progress as progress_module

    output = StringIO()
    monkeypatch.setattr(progress_module, "get_rich_console", lambda **kwargs: Console(file=output, width=200))
    clock = iter(range(100))
    monkeypatch.setattr(progress_module, "monotonic", lambda: float(next(clock)))
    storage = Mock(spec=ITimeComplexityStorage)
    step = BatchingStep(range(5), storage, write_batch_size=2)
    original_make_task = step._make_task

    def make_task(spec):
        assert "Tasks: 0/5" in output.getvalue()
        return original_make_task(spec)

    step._make_task = make_task
    snapshots = []

    def save(models, *, batch_size):
        snapshots.append(output.getvalue())
        assert "Done" not in output.getvalue()

    storage.bulk_insert.side_effect = save
    step.run()
    assert "Tasks: 2/5" in snapshots[0]
    assert "Saved: 0/5" in snapshots[0]
    assert "Tasks: 5/5" in snapshots[-1]
    assert "Saved: 4/5" in snapshots[-1]
    assert "Saving results" in snapshots[-1]
    assert "Done" in output.getvalue()
    assert "Saved: 5/5" in output.getvalue()
    assert "\x1b" not in output.getvalue()


@pytest.mark.parametrize("failed_batch", [1, 3])
def test_save_failure_is_not_retried_or_reported_as_success(serial_scheduler, failed_batch, capsys):
    storage = Mock(spec=ITimeComplexityStorage)
    storage.bulk_insert.side_effect = [None] * (failed_batch - 1) + [RuntimeError("Save failed")]
    with pytest.raises(RuntimeError, match="Save failed"):
        BatchingStep(range(5), storage, write_batch_size=2).run()
    assert storage.bulk_insert.call_count == failed_batch
    output = capsys.readouterr().err
    assert "Interrupted" in output
    assert "Done" not in output
    assert f"Saved: {(failed_batch - 1) * 2}/5" in output


def test_worker_failure_saves_partial_batch_without_success(serial_scheduler, capsys):
    storage = Mock(spec=ITimeComplexityStorage)
    with pytest.raises(RuntimeError, match="Task failed"):
        BatchingStep([0, 1, 2, -1], storage, write_batch_size=2).run()
    output = capsys.readouterr().err
    assert "Interrupted" in output
    assert "Tasks: 3/4" in output
    assert "Saved: 3/4" in output
    assert "Done" not in output


def test_empty_execution_does_not_start_scheduler(monkeypatch, capsys):
    scheduler = Mock()
    monkeypatch.setattr(parallel_execution_step, "Scheduler", scheduler)
    BatchingStep([], Mock()).run()
    scheduler.assert_not_called()
    assert "execution is not required" in capsys.readouterr().err
