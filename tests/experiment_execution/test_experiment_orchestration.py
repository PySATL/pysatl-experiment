"""Tests for experiment orchestration logic."""

import itertools
from unittest.mock import MagicMock, call

import pytest

from pysatl_experiment.experiment_execution.experiment import Experiment
from pysatl_experiment.experiment_execution.experiment_steps import ExperimentSteps
from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.persistence.models.experiment import IExperimentStorage


EXPERIMENT_ID = 42

STEP_PRESENCE_COMBINATIONS = list(itertools.product([False, True], repeat=3))

EXPECTED_STEP_MESSAGES = {
    "generation": ("Running generation step...", "Generation step finished."),
    "execution": ("Running execution step...", "Execution step finished."),
    "report_building": ("Running report building step...", "Report building step finished."),
}

STORAGE_METHODS = {
    "generation": "set_generation_done",
    "execution": "set_execution_done",
    "report_building": "set_report_building_done",
}


def make_step() -> MagicMock:
    """Build a step double implementing IExperimentStep."""
    return MagicMock(spec=IExperimentStep)


def make_storage() -> MagicMock:
    """Build a storage double implementing IExperimentStorage."""
    return MagicMock(spec=IExperimentStorage)


def build_experiment(
    generation_step: IExperimentStep | None = None,
    execution_step: IExperimentStep | None = None,
    report_building_step: IExperimentStep | None = None,
    storage: MagicMock | None = None,
) -> Experiment:
    """Build an experiment from the provided doubles, creating a storage double by default."""
    return Experiment(
        ExperimentSteps(
            experiment_id=EXPERIMENT_ID,
            experiment_storage=storage if storage is not None else make_storage(),
            generation_step=generation_step,
            execution_step=execution_step,
            report_building_step=report_building_step,
        )
    )


def build_presence_case(
    generation: bool,
    execution: bool,
    report_building: bool,
) -> tuple[Experiment, MagicMock, dict[str, MagicMock], dict[str, bool]]:
    """Build an experiment whose steps are enabled or disabled by the given flags."""
    present_steps = {
        "generation": make_step(),
        "execution": make_step(),
        "report_building": make_step(),
    }
    flags = {"generation": generation, "execution": execution, "report_building": report_building}
    steps: dict[str, MagicMock | None] = {name: step if flags[name] else None for name, step in present_steps.items()}

    storage = make_storage()
    experiment = Experiment(
        ExperimentSteps(
            experiment_id=EXPERIMENT_ID,
            experiment_storage=storage,
            generation_step=steps["generation"],
            execution_step=steps["execution"],
            report_building_step=steps["report_building"],
        )
    )

    return experiment, storage, present_steps, flags


# Checks that the constructor stores the provided steps container as-is.
def test_constructor_stores_experiment_steps() -> None:
    steps = ExperimentSteps(
        experiment_id=EXPERIMENT_ID,
        experiment_storage=make_storage(),
        generation_step=None,
        execution_step=None,
        report_building_step=None,
    )

    experiment = Experiment(steps)

    assert experiment.experiment_steps is steps


# Checks that the constructor rejects a missing steps container.
def test_constructor_requires_experiment_steps() -> None:
    with pytest.raises(TypeError):
        Experiment()  # type: ignore[call-arg]


# Checks that only enabled steps run and only their statuses are persisted.
@pytest.mark.parametrize(("generation", "execution", "report_building"), STEP_PRESENCE_COMBINATIONS)
def test_only_enabled_steps_run_and_report_status(
    generation: bool,
    execution: bool,
    report_building: bool,
) -> None:
    experiment, storage, present_steps, flags = build_presence_case(generation, execution, report_building)

    experiment.run_experiment()

    for name, step in present_steps.items():
        storage_method = getattr(storage, STORAGE_METHODS[name])
        if flags[name]:
            step.run.assert_called_once_with()
            storage_method.assert_called_once_with(EXPERIMENT_ID)
        else:
            step.run.assert_not_called()
            storage_method.assert_not_called()


# Checks the exact order of step execution and status persistence.
def test_steps_and_statuses_are_executed_sequentially() -> None:
    generation_step = make_step()
    execution_step = make_step()
    report_building_step = make_step()
    storage = make_storage()
    experiment = build_experiment(generation_step, execution_step, report_building_step, storage)

    manager = MagicMock()
    manager.attach_mock(generation_step, "generation_step")
    manager.attach_mock(execution_step, "execution_step")
    manager.attach_mock(report_building_step, "report_building_step")
    manager.attach_mock(storage, "storage")

    experiment.run_experiment()

    assert manager.mock_calls == [
        call.generation_step.run(),
        call.storage.set_generation_done(EXPERIMENT_ID),
        call.execution_step.run(),
        call.storage.set_execution_done(EXPERIMENT_ID),
        call.report_building_step.run(),
        call.storage.set_report_building_done(EXPERIMENT_ID),
    ]


# Checks that progress messages are printed around each enabled step.
def test_messages_are_printed_for_each_enabled_step(capsys: pytest.CaptureFixture[str]) -> None:
    generation_step = make_step()
    execution_step = make_step()
    experiment = build_experiment(generation_step, execution_step)

    experiment.run_experiment()

    assert capsys.readouterr().out.splitlines() == [
        "Running generation step...",
        "Generation step finished.",
        "Running execution step...",
        "Execution step finished.",
    ]


# Checks that every step of the pipeline produces its start and finish message.
@pytest.mark.parametrize("step_name", list(EXPECTED_STEP_MESSAGES))
def test_each_step_prints_expected_messages(step_name: str, capsys: pytest.CaptureFixture[str]) -> None:
    flags = {name: name == step_name for name in EXPECTED_STEP_MESSAGES}
    experiment, _, _, _ = build_presence_case(flags["generation"], flags["execution"], flags["report_building"])

    experiment.run_experiment()

    start_message, finish_message = EXPECTED_STEP_MESSAGES[step_name]
    assert capsys.readouterr().out == f"{start_message}\n{finish_message}\n"


# Checks that an experiment without steps runs silently and touches no storage.
def test_empty_pipeline_runs_silently(capsys: pytest.CaptureFixture[str]) -> None:
    experiment, storage, _, _ = build_presence_case(False, False, False)

    assert experiment.run_experiment() is None

    assert capsys.readouterr().out == ""
    assert storage.mock_calls == []


# Checks that run_experiment returns None on a successful full run.
def test_run_experiment_returns_none() -> None:
    experiment, _, _, _ = build_presence_case(True, True, True)

    assert experiment.run_experiment() is None


# Checks that a failing step propagates and prevents the remaining pipeline from running.
def test_failing_generation_step_stops_the_pipeline(capsys: pytest.CaptureFixture[str]) -> None:
    generation_step = make_step()
    execution_step = make_step()
    storage = make_storage()
    generation_step.run.side_effect = RuntimeError("generation failed")
    experiment = build_experiment(generation_step, execution_step, storage=storage)

    with pytest.raises(RuntimeError, match="generation failed"):
        experiment.run_experiment()

    assert capsys.readouterr().out == "Running generation step...\n"
    storage.set_generation_done.assert_not_called()
    execution_step.run.assert_not_called()
    storage.set_execution_done.assert_not_called()


# Checks that a failing execution step still keeps the generation status persisted.
def test_failing_execution_step_keeps_generation_status(capsys: pytest.CaptureFixture[str]) -> None:
    generation_step = make_step()
    execution_step = make_step()
    report_building_step = make_step()
    storage = make_storage()
    execution_step.run.side_effect = ValueError("execution failed")
    experiment = build_experiment(generation_step, execution_step, report_building_step, storage)

    with pytest.raises(ValueError, match="execution failed"):
        experiment.run_experiment()

    storage.set_generation_done.assert_called_once_with(EXPERIMENT_ID)
    storage.set_execution_done.assert_not_called()
    report_building_step.run.assert_not_called()


# Checks that a failing report building step keeps the previous statuses persisted.
def test_failing_report_building_step_keeps_previous_statuses() -> None:
    generation_step = make_step()
    execution_step = make_step()
    report_building_step = make_step()
    storage = make_storage()
    report_building_step.run.side_effect = KeyError("report failed")
    experiment = build_experiment(generation_step, execution_step, report_building_step, storage)

    with pytest.raises(KeyError):
        experiment.run_experiment()

    storage.set_generation_done.assert_called_once_with(EXPERIMENT_ID)
    storage.set_execution_done.assert_called_once_with(EXPERIMENT_ID)
    storage.set_report_building_done.assert_not_called()
