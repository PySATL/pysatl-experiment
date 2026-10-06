"""Tests for the power experiment execution step."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pysatl_criterion import DistributionType

from pysatl_experiment.configuration.models.alternative import Alternative
from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.experiment_execution.parallel.task_spec import TaskSpec
from pysatl_experiment.experiment_execution.step.execution_step.multithreading_execution_step import ExecutionTaskResult
from pysatl_experiment.experiment_execution.step.execution_step.power import power_execution_step
from pysatl_experiment.experiment_execution.step.execution_step.power.power_execution_step import (
    PowerExecutionStep,
    PowerStepData,
)
from pysatl_experiment.experiment_execution.step.execution_step.power.power_worker import PowerWorkerResult
from pysatl_experiment.persistence.models.power import IPowerStorage
from pysatl_experiment.persistence.models.random_values import IRandomValuesStorage


class FakeStatistic:
    """Minimal statistic stub exposing the ``code`` method used to build task specs."""

    def __init__(self, code: str = "KS") -> None:
        self._code = code

    def code(self) -> str:
        return self._code


def make_step_data(sample_size: int = 10, significance_level: float = 0.05) -> PowerStepData:
    """Build a power step data entry with a fake statistic and a real alternative."""
    return PowerStepData(
        statistics=FakeStatistic(),  # type: ignore[arg-type]
        sample_size=sample_size,
        criterion_parameters=[0.0, 1.0],
        alternative=Alternative(parameters=[0.0, 1.0], distribution_type=DistributionType.NORMAL),
        significance_level=significance_level,
    )


def make_spec(significance_level: float | None = 0.05) -> TaskSpec:
    """Build a task spec carrying the fields consumed by the step."""
    return TaskSpec(
        experiment_type=ExperimentType.POWER,
        statistic_class_name="FakeStatistic",
        statistic_module="fake_module",
        sample_size=10,
        monte_carlo_count=5,
        db_path="sqlite:///db.sqlite",
        experiment_name="power_exp",
        criterion_code="KS",
        criterion_parameters=[0.0, 1.0],
        sample_generator_code="NORMAL",
        sample_generator_parameters=[0.0, 1.0],
        alternative_generator="NORMAL",
        alternative_parameters=[0.0, 1.0],
        significance_level=significance_level,
    )


def make_step(step_config: list[PowerStepData] | None = None, **overrides: Any) -> PowerExecutionStep:
    """Build a power execution step wired to mock storages."""
    values: dict[str, Any] = {
        "experiment_id": 3,
        "experiment_name": "power_exp",
        "step_config": [] if step_config is None else step_config,
        "monte_carlo_count": 5,
        "data_storage": MagicMock(spec=IRandomValuesStorage),
        "result_storage": MagicMock(spec=IPowerStorage),
        "storage_connection": "sqlite:///db.sqlite",
        "parallel_workers": 1,
    }
    values.update(overrides)

    return PowerExecutionStep(**values)


# Checks that the constructor stores every provided configuration argument.
def test_constructor_stores_configuration() -> None:
    data_storage = MagicMock(spec=IRandomValuesStorage)
    step_config = [make_step_data()]

    step = make_step(step_config=step_config, data_storage=data_storage)

    assert step.data_storage is data_storage
    assert step.experiment_id == 3
    assert step.experiment_name == "power_exp"
    assert step.step_config is step_config
    assert step.monte_carlo_count == 5
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
    alternative = Alternative(parameters=[1.0, 2.0], distribution_type=DistributionType.NORMAL)
    step_data = PowerStepData(
        statistics=FakeStatistic(),  # type: ignore[arg-type]
        sample_size=42,
        criterion_parameters=[3.0, 4.0],
        alternative=alternative,
        significance_level=0.01,
    )

    spec = make_step(step_config=[step_data], monte_carlo_count=7)._collect_tasks()[0]

    assert spec.experiment_type is ExperimentType.POWER
    assert spec.experiment_name == "power_exp"
    assert spec.statistic_class_name == "FakeStatistic"
    assert spec.criterion_code == "KS"
    assert spec.criterion_parameters == [3.0, 4.0]
    assert spec.sample_size == 42
    assert spec.monte_carlo_count == 7
    assert spec.db_path == "sqlite:///db.sqlite"
    assert spec.sample_generator_code == DistributionType.NORMAL
    assert spec.alternative_generator == DistributionType.NORMAL
    assert spec.alternative_parameters == [1.0, 2.0]
    assert spec.significance_level == 0.01


# Checks that executing a task builds the power worker and wraps its result.
def test_execute_task_builds_worker_and_returns_result() -> None:
    spec = make_spec()
    statistics = FakeStatistic()
    samples = [[1.0, 2.0], [3.0, 4.0]]
    worker_result = PowerWorkerResult(results_criteria=[True, False])

    with patch.object(PowerExecutionStep, "_load_samples_and_statistics", return_value=(samples, statistics)):
        with patch.object(power_execution_step, "PowerWorker") as worker_factory:
            worker_factory.return_value.execute.return_value = worker_result

            result = PowerExecutionStep._execute_task(spec)

    worker_factory.assert_called_once_with(
        statistics=statistics,
        sample_data=samples,
        significance_level=0.05,
        storage_connection="sqlite:///db.sqlite",
    )
    assert result.spec is spec
    assert result.worker_result is worker_result


# Checks that a task without a significance level is rejected before running the worker.
def test_execute_task_raises_for_missing_significance_level() -> None:
    with patch.object(PowerExecutionStep, "_load_samples_and_statistics", return_value=([], FakeStatistic())):
        with pytest.raises(ValueError, match="Significance level is required"):
            PowerExecutionStep._execute_task(make_spec(significance_level=None))


# Checks that a worker result is converted into a populated power model.
def test_to_model_builds_power_model() -> None:
    step = make_step()
    spec = make_spec()
    result = ExecutionTaskResult(spec=spec, worker_result=PowerWorkerResult(results_criteria=[True, False]))

    model = step._to_model(result)

    assert model.experiment_id == 3
    assert model.criterion_code == "KS"
    assert model.criterion_parameters == [0.0, 1.0]
    assert model.sample_size == 10
    assert model.alternative_code == "NORMAL"
    assert model.alternative_parameters == [0.0, 1.0]
    assert model.monte_carlo_count == 5
    assert model.significance_level == 0.05
    assert model.results_criteria == [True, False]


# Checks that converting a result without a significance level raises an error.
def test_to_model_raises_for_missing_significance_level() -> None:
    step = make_step()
    result = ExecutionTaskResult(
        spec=make_spec(significance_level=None),
        worker_result=PowerWorkerResult(results_criteria=[]),
    )

    with pytest.raises(ValueError, match="significance_level is required"):
        step._to_model(result)


# Checks that bulk saving delegates the prepared models to the result storage.
def test_bulk_save_delegates_to_storage() -> None:
    storage = MagicMock(spec=IPowerStorage)
    step = make_step(result_storage=storage)
    models = [MagicMock(), MagicMock()]

    step._bulk_save(models)

    storage.bulk_insert_data.assert_called_once_with(models)
