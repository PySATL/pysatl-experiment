"""Tests for the critical value experiment execution step."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.experiment_execution.parallel.task_spec import TaskSpec
from pysatl_experiment.experiment_execution.step.execution_step.critical_value import critical_value_execution_step
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.critical_value_execution_step import (
    CriticalValueExecutionStep,
    CriticalValueStepData,
)
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.critical_value_worker import (
    CriticalValueWorkerResult,
)
from pysatl_experiment.experiment_execution.step.execution_step.execution_step_data import HypothesisGeneratorData
from pysatl_experiment.experiment_execution.step.execution_step.multithreading_execution_step import ExecutionTaskResult
from pysatl_experiment.persistence.models.random_values import IRandomValuesStorage


class FakeStatistic:
    """Minimal statistic stub exposing the ``code`` method used to build task specs."""

    def __init__(self, code: str = "KS") -> None:
        self._code = code

    def code(self) -> str:
        return self._code


def make_step_data(sample_size: int = 10) -> CriticalValueStepData:
    """Build a critical value step data entry with a fake statistic."""
    return CriticalValueStepData(
        statistics=FakeStatistic(),  # type: ignore[arg-type]
        sample_size=sample_size,
        criterion_parameters=[0.0, 1.0],
    )


def make_generator_data() -> HypothesisGeneratorData:
    """Build hypothesis generator data used to derive task spec generator fields."""
    return HypothesisGeneratorData(generator_name="NORMAL", parameters=[2.0, 3.0])


def make_spec() -> TaskSpec:
    """Build a task spec carrying the fields consumed by the step."""
    return TaskSpec(
        experiment_type=ExperimentType.CRITICAL_VALUE,
        statistic_class_name="FakeStatistic",
        statistic_module="fake_module",
        sample_size=10,
        monte_carlo_count=6,
        db_path="sqlite:///db.sqlite",
        experiment_name="cv_exp",
        criterion_code="KS",
        criterion_parameters=[0.0, 1.0],
        sample_generator_code="NORMAL",
        sample_generator_parameters=[2.0, 3.0],
        hypothesis_generator="NORMAL",
        hypothesis_parameters=[2.0, 3.0],
    )


def make_step(step_config: list[CriticalValueStepData] | None = None, **overrides: Any) -> CriticalValueExecutionStep:
    """Build a critical value execution step wired to mock storages."""
    values: dict[str, Any] = {
        "experiment_id": 9,
        "experiment_name": "cv_exp",
        "hypothesis_generator_data": make_generator_data(),
        "step_config": [] if step_config is None else step_config,
        "monte_carlo_count": 6,
        "data_storage": MagicMock(spec=IRandomValuesStorage),
        "result_storage": MagicMock(),
        "storage_connection": "sqlite:///db.sqlite",
        "parallel_workers": 1,
    }
    values.update(overrides)

    return CriticalValueExecutionStep(**values)


# Checks that the constructor stores every provided configuration argument.
def test_constructor_stores_configuration() -> None:
    data_storage = MagicMock(spec=IRandomValuesStorage)
    generator_data = make_generator_data()
    step_config = [make_step_data()]

    step = make_step(
        step_config=step_config,
        data_storage=data_storage,
        hypothesis_generator_data=generator_data,
    )

    assert step.data_storage is data_storage
    assert step.hypothesis_generator_data is generator_data
    assert step.experiment_id == 9
    assert step.experiment_name == "cv_exp"
    assert step.step_config is step_config
    assert step.monte_carlo_count == 6
    assert step.storage_connection == "sqlite:///db.sqlite"
    assert step.parallel_workers == 1


# Checks that exactly one task spec is produced for every step data entry.
@pytest.mark.parametrize("count", [0, 1, 3])
def test_collect_tasks_builds_one_spec_per_step_data(count: int) -> None:
    step_config = [make_step_data(sample_size=10 * (index + 1)) for index in range(count)]

    task_specs = make_step(step_config=step_config)._collect_tasks()

    assert len(task_specs) == count
    assert all(isinstance(spec, TaskSpec) for spec in task_specs)


# Checks that every step data field is mapped onto the produced task spec.
def test_collect_tasks_maps_step_data_into_spec() -> None:
    step_data = CriticalValueStepData(
        statistics=FakeStatistic(),  # type: ignore[arg-type]
        sample_size=42,
        criterion_parameters=[3.0, 4.0],
    )

    spec = make_step(step_config=[step_data], monte_carlo_count=7)._collect_tasks()[0]

    assert spec.experiment_type is ExperimentType.CRITICAL_VALUE
    assert spec.experiment_name == "cv_exp"
    assert spec.statistic_class_name == "FakeStatistic"
    assert spec.criterion_code == "KS"
    assert spec.criterion_parameters == [3.0, 4.0]
    assert spec.sample_size == 42
    assert spec.monte_carlo_count == 7
    assert spec.db_path == "sqlite:///db.sqlite"
    assert spec.sample_generator_code == "NORMAL"
    assert spec.sample_generator_parameters == [2.0, 3.0]
    assert spec.hypothesis_generator == "NORMAL"
    assert spec.hypothesis_parameters == [2.0, 3.0]


# Checks that executing a task builds the critical value worker and wraps its result.
def test_execute_task_builds_worker_and_returns_result() -> None:
    spec = make_spec()
    statistics = FakeStatistic()
    samples = [[1.0, 2.0], [3.0, 4.0]]
    worker_result = CriticalValueWorkerResult(results_statistics=[1.5, 2.5])

    with patch.object(CriticalValueExecutionStep, "_load_samples_and_statistics", return_value=(samples, statistics)):
        with patch.object(critical_value_execution_step, "CriticalValueWorker") as worker_factory:
            worker_factory.return_value.execute.return_value = worker_result

            result = CriticalValueExecutionStep._execute_task(spec)

    worker_factory.assert_called_once_with(statistics=statistics, sample_data=samples)
    assert result.spec is spec
    assert result.worker_result is worker_result


# Checks that a worker result is converted into a populated limit distribution model.
def test_to_model_builds_limit_distribution_model() -> None:
    step = make_step()
    spec = make_spec()
    result = ExecutionTaskResult(spec=spec, worker_result=CriticalValueWorkerResult(results_statistics=[1.5, 2.5]))

    model = step._to_model(result)

    assert model.experiment_id == 9
    assert model.criterion_code == "KS"
    assert model.criterion_parameters == [0.0, 1.0]
    assert model.sample_size == 10
    assert model.monte_carlo_count == 6
    assert model.results_statistics == [1.5, 2.5]


# Checks that bulk saving delegates the prepared models to the result storage.
def test_bulk_save_delegates_to_storage() -> None:
    storage = MagicMock()
    step = make_step(result_storage=storage)
    models = [MagicMock(), MagicMock()]

    step._bulk_save(models)

    storage.insert_bulk_data.assert_called_once_with(models)
