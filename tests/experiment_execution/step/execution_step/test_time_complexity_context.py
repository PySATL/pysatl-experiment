"""Prepared task execution constructs dependencies and statistics in the child process."""

import os
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock

import pytest

from pysatl_experiment.experiment_execution.criterion_spec import CriterionSpec
from pysatl_experiment.experiment_execution.step.execution_step.time_complexity.context import (
    TimeComplexityExecutionContext,
)
from pysatl_experiment.experiment_execution.step.execution_step.time_complexity.task_spec import TimeComplexityTask
from pysatl_experiment.experiment_execution.step.execution_step.time_complexity.time_complexity_execution_step import (
    TimeComplexityExecutionStep,
)
from pysatl_experiment.persistence.models.random_values import RandomValuesModel
from pysatl_experiment.persistence.sqlalchemy.random_values import AlchemyRandomValuesStorage
from pysatl_experiment.sample_loading.sqlalchemy_source import SqlAlchemySampleSourceFactory
from pysatl_experiment.types import Sample, SampleBatch, SampleSetSpec


class ParameterizedStatistic:
    def __init__(self, location, scale, parent_pid=0):
        assert os.getpid() != parent_pid
        self.location = location
        self.scale = scale

    def execute_statistic(self, rvs):
        assert self.location == 2.0 and self.scale == 3.0
        assert rvs == [1.0, 2.0]
        return sum(rvs)


@dataclass(frozen=True)
class ChildSourceFactory:
    connection: str
    parent_pid: int
    initialization_log: str

    def __call__(self):
        assert os.getpid() != self.parent_pid
        with Path(self.initialization_log).open("a") as log:
            log.write("initialized\n")
        return SqlAlchemySampleSourceFactory(self.connection)()


def task(**parameters):
    return TimeComplexityTask(
        CriterionSpec("test", ParameterizedStatistic, dict(location=2.0, scale=3.0) | parameters),
        SampleSetSpec(
            experiment_name="experiment",
            generator_code="normal",
            sample_size=2,
            samples_count=2,
        ),
    )


def test_injected_source_and_parameters_are_used():
    spec = task()
    source = Mock()
    source.load.return_value = SampleBatch(spec.sample_set, [Sample([1.0, 2.0]), Sample([1.0, 2.0])])
    factory = Mock(return_value=source)
    step = TimeComplexityExecutionStep(TimeComplexityExecutionContext("experiment", 1, (spec,)), factory, Mock())
    result = step._make_task(spec)(step.context_factory())
    factory.assert_called_once_with()
    source.load.assert_called_once_with(spec.sample_set)
    model = step._to_model(result)
    assert model.criterion_parameters == {"location": 2.0, "scale": 3.0}
    assert len(model.results_times) == model.samples_count == 2


def test_real_process_reuses_source_and_constructs_parameterized_statistic(tmp_path):
    connection = f"sqlite:///{tmp_path / 'samples.db'}"
    storage = AlchemyRandomValuesStorage(connection)
    storage.init()
    storage.bulk_insert([RandomValuesModel("experiment", "normal", {}, 2, [1.0, 2.0]) for _ in range(2)])
    spec = task(parent_pid=os.getpid())
    initialization_log = tmp_path / "initializations.txt"
    result_storage = Mock()
    step = TimeComplexityExecutionStep(
        TimeComplexityExecutionContext("experiment", 1, (spec, spec, spec), write_batch_size=2),
        ChildSourceFactory(connection, os.getpid(), str(initialization_log)),
        result_storage,
    )
    step.run()
    assert initialization_log.read_text().splitlines() == ["initialized"]
    assert [len(call.args[0]) for call in result_storage.bulk_insert.call_args_list] == [2, 1]
    assert all(call.kwargs == {"batch_size": 2} for call in result_storage.bulk_insert.call_args_list)
    model = result_storage.bulk_insert.call_args.args[0][0]
    assert model.experiment_name == "experiment"
    assert model.criterion_parameters == spec.criterion.parameters
    assert len(model.results_times) == 2


def test_context_rejects_another_experiment():
    with pytest.raises(ValueError, match="belong"):
        TimeComplexityExecutionContext("other", 1, (task(),))


@pytest.mark.parametrize("workers", [0, -1, True])
def test_context_rejects_invalid_parallelism(workers):
    with pytest.raises(ValueError, match="parallel_workers"):
        TimeComplexityExecutionContext("experiment", workers, ())


def test_missing_samples_prevent_result_saving():
    spec = task()
    source = Mock()
    source.load.side_effect = ValueError("Not enough data")
    result_storage = Mock()
    step = TimeComplexityExecutionStep(
        TimeComplexityExecutionContext("experiment", 1, (spec,)), Mock(return_value=source), result_storage
    )
    with pytest.raises(ValueError, match="Not enough data"):
        step._make_task(spec)(step.context_factory())
    result_storage.bulk_insert.assert_not_called()


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "2", None])
def test_context_rejects_invalid_write_batch_size(value):
    with pytest.raises(ValueError, match="write_batch_size"):
        TimeComplexityExecutionContext("experiment", 1, (), write_batch_size=value)
