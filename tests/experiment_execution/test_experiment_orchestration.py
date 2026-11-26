"""Tests for experiment orchestration logic."""

import itertools
import logging
from unittest.mock import MagicMock, call

import pytest

from pysatl_experiment.configuration.models.step_status import ExperimentStep, StepStatus
from pysatl_experiment.experiment_execution.experiment import Experiment
from pysatl_experiment.experiment_execution.experiment_steps import ExperimentSteps
from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.persistence.models.experiment import IExperimentStorage


EXPERIMENT_ID = 42

EXPERIMENT_LOGGER = "pysatl_experiment.experiment_execution.experiment"

STEP_PRESENCE_COMBINATIONS = list(itertools.product([False, True], repeat=3))

STEP_ORDER = ("generation", "execution", "report_building")

STORAGE_STEPS = {
    "generation": ExperimentStep.GENERATION,
    "execution": ExperimentStep.EXECUTION,
    "report_building": ExperimentStep.REPORT_BUILDING,
}


def _expected_messages(step: str, start: str, finish: str) -> tuple[str, str]:
    """Build expected log messages with the experiment context prefix."""
    prefix = f"[experiment_id={EXPERIMENT_ID}, step={step}]"
    return f"{prefix} {start}", f"{prefix} {finish}"


EXPECTED_STEP_MESSAGES = {
    "generation": _expected_messages("generation", "Running generation step...", "Generation step finished."),
    "execution": _expected_messages("execution", "Running execution step...", "Execution step finished."),
    "report_building": _expected_messages(
        "report_building", "Running report building step...", "Report building step finished."
    ),
}

EXPECTED_FAILURE_MESSAGES = {
    "generation": f"[experiment_id={EXPERIMENT_ID}, step=generation] Generation step failed.",
    "execution": f"[experiment_id={EXPERIMENT_ID}, step=execution] Execution step failed.",
    "report_building": f"[experiment_id={EXPERIMENT_ID}, step=report_building] Report building step failed.",
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


def expected_status_calls(step_name: str) -> list:
    """Build the expected RUNNING -> DONE status call sequence for a step."""
    return [
        call(EXPERIMENT_ID, STORAGE_STEPS[step_name], StepStatus.RUNNING),
        call(EXPERIMENT_ID, STORAGE_STEPS[step_name], StepStatus.DONE),
    ]


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

    expected_storage_calls: list = []
    for name in STEP_ORDER:
        if flags[name]:
            present_steps[name].run.assert_called_once_with()
            expected_storage_calls.extend(expected_status_calls(name))
        else:
            present_steps[name].run.assert_not_called()

    assert storage.set_step_status.call_args_list == expected_storage_calls


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
        call.storage.set_step_status(EXPERIMENT_ID, ExperimentStep.GENERATION, StepStatus.RUNNING),
        call.generation_step.run(),
        call.storage.set_step_status(EXPERIMENT_ID, ExperimentStep.GENERATION, StepStatus.DONE),
        call.storage.set_step_status(EXPERIMENT_ID, ExperimentStep.EXECUTION, StepStatus.RUNNING),
        call.execution_step.run(),
        call.storage.set_step_status(EXPERIMENT_ID, ExperimentStep.EXECUTION, StepStatus.DONE),
        call.storage.set_step_status(EXPERIMENT_ID, ExperimentStep.REPORT_BUILDING, StepStatus.RUNNING),
        call.report_building_step.run(),
        call.storage.set_step_status(EXPERIMENT_ID, ExperimentStep.REPORT_BUILDING, StepStatus.DONE),
    ]


# Checks that progress messages are logged around each enabled step.
def test_messages_are_logged_for_each_enabled_step(caplog: pytest.LogCaptureFixture) -> None:
    generation_step = make_step()
    execution_step = make_step()
    experiment = build_experiment(generation_step, execution_step)

    with caplog.at_level(logging.INFO, logger=EXPERIMENT_LOGGER):
        experiment.run_experiment()

    assert [record.message for record in caplog.records] == [
        EXPECTED_STEP_MESSAGES["generation"][0],
        EXPECTED_STEP_MESSAGES["generation"][1],
        EXPECTED_STEP_MESSAGES["execution"][0],
        EXPECTED_STEP_MESSAGES["execution"][1],
    ]
    assert all(record.levelno == logging.INFO for record in caplog.records)


# Checks that context fields are attached to every emitted record.
def test_log_records_carry_experiment_context(caplog: pytest.LogCaptureFixture) -> None:
    generation_step = make_step()
    experiment = build_experiment(generation_step=generation_step)

    with caplog.at_level(logging.INFO, logger=EXPERIMENT_LOGGER):
        experiment.run_experiment()

    assert len(caplog.records) == 2
    for record in caplog.records:
        # Context fields are attached dynamically via the extra mechanism.
        assert record.experiment_id == EXPERIMENT_ID  # type: ignore[attr-defined]
        assert record.step == "generation"  # type: ignore[attr-defined]


# Checks that every step of the pipeline produces its start and finish message.
@pytest.mark.parametrize("step_name", list(EXPECTED_STEP_MESSAGES))
def test_each_step_logs_expected_messages(step_name: str, caplog: pytest.LogCaptureFixture) -> None:
    flags = {name: name == step_name for name in EXPECTED_STEP_MESSAGES}
    experiment, _, _, _ = build_presence_case(flags["generation"], flags["execution"], flags["report_building"])

    with caplog.at_level(logging.INFO, logger=EXPERIMENT_LOGGER):
        experiment.run_experiment()

    start_message, finish_message = EXPECTED_STEP_MESSAGES[step_name]
    assert [record.message for record in caplog.records] == [start_message, finish_message]


# Checks that an experiment without steps runs silently and touches no storage.
def test_empty_pipeline_runs_silently(caplog: pytest.LogCaptureFixture) -> None:
    experiment, storage, _, _ = build_presence_case(False, False, False)

    with caplog.at_level(logging.INFO, logger=EXPERIMENT_LOGGER):
        assert experiment.run_experiment() is None

    assert caplog.records == []
    assert storage.mock_calls == []


# Checks that run_experiment returns None on a successful full run.
def test_run_experiment_returns_none() -> None:
    experiment, _, _, _ = build_presence_case(True, True, True)

    assert experiment.run_experiment() is None


# Checks that a failing step propagates and prevents the remaining pipeline from running.
def test_failing_generation_step_stops_the_pipeline(caplog: pytest.LogCaptureFixture) -> None:
    generation_step = make_step()
    execution_step = make_step()
    storage = make_storage()
    generation_step.run.side_effect = RuntimeError("generation failed")
    experiment = build_experiment(generation_step, execution_step, storage=storage)

    with (
        caplog.at_level(logging.INFO, logger=EXPERIMENT_LOGGER),
        pytest.raises(RuntimeError, match="generation failed"),
    ):
        experiment.run_experiment()

    assert [record.message for record in caplog.records] == [
        EXPECTED_STEP_MESSAGES["generation"][0],
        EXPECTED_FAILURE_MESSAGES["generation"],
    ]
    assert caplog.records[-1].levelno == logging.ERROR
    assert storage.set_step_status.call_args_list == [
        call(EXPERIMENT_ID, ExperimentStep.GENERATION, StepStatus.RUNNING),
        call(EXPERIMENT_ID, ExperimentStep.GENERATION, StepStatus.FAILED),
    ]
    execution_step.run.assert_not_called()


# Checks that a failing execution step still keeps the generation status persisted.
def test_failing_execution_step_keeps_generation_status() -> None:
    generation_step = make_step()
    execution_step = make_step()
    report_building_step = make_step()
    storage = make_storage()
    execution_step.run.side_effect = ValueError("execution failed")
    experiment = build_experiment(generation_step, execution_step, report_building_step, storage)

    with pytest.raises(ValueError, match="execution failed"):
        experiment.run_experiment()

    assert storage.set_step_status.call_args_list == [
        *expected_status_calls("generation"),
        call(EXPERIMENT_ID, ExperimentStep.EXECUTION, StepStatus.RUNNING),
        call(EXPERIMENT_ID, ExperimentStep.EXECUTION, StepStatus.FAILED),
    ]
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

    assert storage.set_step_status.call_args_list == [
        *expected_status_calls("generation"),
        *expected_status_calls("execution"),
        call(EXPERIMENT_ID, ExperimentStep.REPORT_BUILDING, StepStatus.RUNNING),
        call(EXPERIMENT_ID, ExperimentStep.REPORT_BUILDING, StepStatus.FAILED),
    ]
