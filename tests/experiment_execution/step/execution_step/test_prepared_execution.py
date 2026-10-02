"""Critical-value and power steps load prepared tasks and preserve their metadata."""

import os
import pickle
from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from pysatl_experiment.experiment_execution.criterion_spec import CriterionSpec
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.context import (
    CriticalValueExecutionContext,
)
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.critical_value_execution_step import (
    CriticalValueExecutionStep,
)
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.task_spec import CriticalValueTask
from pysatl_experiment.experiment_execution.step.execution_step.power import power_execution_step as power_module
from pysatl_experiment.experiment_execution.step.execution_step.power.context import PowerExecutionContext
from pysatl_experiment.experiment_execution.step.execution_step.power.power_execution_step import PowerExecutionStep
from pysatl_experiment.experiment_execution.step.execution_step.power.power_worker import PowerWorkerResult
from pysatl_experiment.experiment_execution.step.execution_step.power.task_spec import PowerTask
from pysatl_experiment.persistence.models.random_values import RandomValuesModel
from pysatl_experiment.persistence.sqlalchemy.random_values import AlchemyRandomValuesStorage
from pysatl_experiment.sample_loading.sqlalchemy_source import SqlAlchemySampleSourceFactory
from pysatl_experiment.types import Sample, SampleBatch, SampleSetSpec


class ConfiguredStatistic:
    def __init__(self, scale, parent_pid=0):
        assert os.getpid() != parent_pid
        self.scale = scale

    def execute_statistic(self, rvs):
        return sum(rvs) * self.scale


@dataclass(frozen=True)
class ChildSource:
    connection: str
    parent_pid: int

    def __call__(self):
        assert os.getpid() != self.parent_pid
        return SqlAlchemySampleSourceFactory(self.connection)()


def make_task(kind, **parameters):
    criterion = CriterionSpec("configured", ConfiguredStatistic, {"scale": 2.0} | parameters)
    samples = SampleSetSpec(experiment_name="experiment", generator_code="normal", sample_size=2, samples_count=2)
    if kind == "critical_value":
        return CriticalValueTask(criterion, samples)
    return PowerTask(criterion, samples, 0.05, {"mean": [0.0, 1.0]})


def make_step(kind, tasks, source, storage):
    if kind == "critical_value":
        return CriticalValueExecutionStep(CriticalValueExecutionContext("experiment", 1, tasks, 2), source, storage)
    return PowerExecutionStep(
        PowerExecutionContext("experiment", 1, tasks, 2), source, storage, storage_connection="sqlite:///critical.db"
    )


@pytest.mark.parametrize("kind", ["critical_value", "power"])
def test_task_loads_samples_constructs_statistic_and_preserves_result_identity(kind, monkeypatch):
    task = make_task(kind)
    source = Mock()
    source.load.return_value = SampleBatch(task.sample_set, [Sample([1.0, 2.0]), Sample([2.0, 3.0])])
    storage = Mock()
    step = make_step(kind, (task,), Mock(return_value=source), storage)
    worker_factory = Mock()
    worker_factory.return_value.execute.return_value = PowerWorkerResult([True, False])
    monkeypatch.setattr(power_module, "PowerWorker", worker_factory)
    # A submitted callable must not capture the step, source, or parent result store.
    execute = pickle.loads(pickle.dumps(step._make_task(task)))  # noqa: S301
    result = execute(source)
    source.load.assert_called_once_with(task.sample_set)
    step.save_batch([result])
    model = storage.bulk_insert_data.call_args.args[0][0]
    assert model.experiment_name == task.sample_set.experiment_name
    assert model.criterion_parameters == task.criterion.parameters
    assert model.sample_size == 2
    assert model.monte_carlo_count == 2
    if kind == "critical_value":
        assert model.results_statistics == [6.0, 10.0]
    else:
        arguments = worker_factory.call_args.kwargs
        assert arguments["statistics"].scale == 2.0
        assert arguments["sample_data"] is source.load.return_value
        assert arguments["significance_level"] == model.significance_level == 0.05
        assert arguments["storage_connection"] == "sqlite:///critical.db"
        assert model.alternative_code == "normal"
        assert model.alternative_parameters == {"mean": [0.0, 1.0]}
        assert model.results_criteria == [True, False]


def test_critical_value_real_process_loads_samples_and_saves_full_and_partial_batches(tmp_path):
    connection = f"sqlite:///{tmp_path / 'samples.db'}"
    data = AlchemyRandomValuesStorage(connection)
    data.init()
    data.bulk_insert([RandomValuesModel("experiment", "normal", {}, 2, [1.0, 2.0])] * 2)
    task = make_task("critical_value", parent_pid=os.getpid())
    storage = Mock()
    step = make_step("critical_value", (task,) * 3, ChildSource(connection, os.getpid()), storage)
    step.run()
    assert [len(call.args[0]) for call in storage.bulk_insert_data.call_args_list] == [2, 1]
    assert all(
        model.results_statistics == [6.0, 6.0]
        for call in storage.bulk_insert_data.call_args_list
        for model in call.args[0]
    )


@pytest.mark.parametrize("kind", ["critical_value", "power"])
def test_missing_samples_prevent_worker_execution_and_saving(kind):
    task = make_task(kind)
    source = Mock()
    source.load.side_effect = ValueError("Not enough data")
    storage = Mock()
    step = make_step(kind, (task,), Mock(return_value=source), storage)
    with pytest.raises(ValueError, match="Not enough data"):
        step._make_task(task)(source)
    storage.bulk_insert_data.assert_not_called()


@pytest.mark.parametrize(
    "context,kind", [(CriticalValueExecutionContext, "critical_value"), (PowerExecutionContext, "power")]
)
def test_context_checks_identity_and_limits(context, kind):
    with pytest.raises(ValueError, match="belong"):
        context("other", 1, (make_task(kind),))
    for value in [0, -1, True, 1.5, "2", None]:
        with pytest.raises(ValueError, match="parallel_workers"):
            context("experiment", value, ())
        with pytest.raises(ValueError, match="write_batch_size"):
            context("experiment", 1, (), value)
