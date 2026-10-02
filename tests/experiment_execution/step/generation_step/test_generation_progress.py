"""Generation progress reflects received and successfully persisted samples."""

from io import StringIO
from unittest.mock import Mock

import pytest
from pysatl_criterion import DistributionType
from pysatl_criterion.utils.generator import get_available_generator
from rich.console import Console
from rich.progress import Progress

from pysatl_experiment.experiment_execution.step import progress as progress_module
from pysatl_experiment.experiment_execution.step.generation_step import multithreading_generation_step as module
from pysatl_experiment.experiment_execution.step.generation_step.generation_step import GenerationStep
from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import (
    GenerationData,
    GenerationStepContext,
)


@pytest.fixture
def progress_run(monkeypatch):
    output = StringIO()
    console = Console(file=output, width=200, force_terminal=False, color_system=None)
    monkeypatch.setattr(module, "get_rich_console", lambda **kwargs: console)
    monkeypatch.setattr(progress_module, "get_rich_console", lambda **kwargs: console)
    displays = []

    def make_progress(*args, **kwargs):
        progress = Progress(*args, **kwargs)
        displays.append(progress)
        return progress

    monkeypatch.setattr(progress_module, "Progress", make_progress)
    scheduler = Mock()
    scheduler.__enter__ = Mock(return_value=scheduler)
    scheduler.__exit__ = Mock(return_value=False)
    scheduler.iterate_results.side_effect = lambda tasks: (task(None) for task in tasks)
    scheduler_factory = Mock(return_value=scheduler)
    monkeypatch.setattr(module, "Scheduler", scheduler_factory)
    return displays, output, scheduler_factory


def make_step(count=5):
    generator = get_available_generator(DistributionType.NORMAL, {"mean": 0, "var": 1})
    return GenerationStep(
        GenerationStepContext(
            data_list=[GenerationData(generator, 2, count, "normal")] if count else [],
            experiment_name="generation_progress",
            samples_per_task=2,
            write_batch_size=3,
        ),
        Mock(),
    )


@pytest.mark.parametrize("fail_on_batch", [None, 1, 2])
def test_progress_advances_only_after_successful_save_including_final_flush(progress_run, fail_on_batch):
    displays, output, _ = progress_run
    step = make_step()
    saved = []
    observations = []

    def save(models, *, batch_size):
        task = displays[0].tasks[0]
        observations.append((task.completed, task.fields["processed"], len(models)))
        assert task.completed == len(saved)
        if len(observations) == fail_on_batch:
            raise RuntimeError("storage failed")
        saved.extend(models)

    step.random_values_storage.bulk_insert.side_effect = save
    if fail_on_batch:
        with pytest.raises(RuntimeError, match="storage failed"):
            step.run()
    else:
        step.run()

    progress = displays[0]
    task = progress.tasks[0]
    assert task.total == 5
    assert task.completed == len(saved)
    assert observations == [(0, 4, 3)] + ([(3, 5, 2)] if fail_on_batch != 1 else [])
    assert task.finished == (fail_on_batch is None)
    assert not progress.live.is_started
    assert "\x1b" not in output.getvalue()
    if fail_on_batch:
        assert "Interrupted" in output.getvalue()
        assert "100%" not in output.getvalue()
    else:
        assert "Generated: 5/5" in output.getvalue()
        assert "Saved: 5/5" in output.getvalue()


def test_empty_plan_skips_worker_pool_and_progress(progress_run):
    displays, output, scheduler_factory = progress_run
    step = make_step(count=0)
    step.run()
    assert displays == []
    scheduler_factory.assert_not_called()
    step.random_values_storage.bulk_insert.assert_not_called()
    assert "generation is not required" in output.getvalue()


def test_worker_failure_keeps_partial_progress_and_closes_display(progress_run):
    displays, output, scheduler_factory = progress_run
    step = make_step()

    def failing_results(tasks):
        yield next(iter(tasks))(None)
        raise RuntimeError("worker failed")

    scheduler_factory.return_value.iterate_results.side_effect = failing_results
    with pytest.raises(RuntimeError, match="worker failed"):
        step.run()
    task = displays[0].tasks[0]
    assert task.fields["processed"] == 2
    assert task.completed == 0
    assert not task.finished
    assert not displays[0].live.is_started
    step.random_values_storage.bulk_insert.assert_not_called()
    assert "Interrupted" in output.getvalue()
