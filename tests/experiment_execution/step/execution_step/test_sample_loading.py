"""Execution sample loading respects the experiment and requested sample count."""

from dataclasses import replace

import pytest

from pysatl_experiment.experiment_execution.criterion_spec import CriterionSpec
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.critical_value_execution_step import (
    CriticalValueExecutionStep,
)
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.task_spec import CriticalValueTask
from pysatl_experiment.persistence.models.random_values import RandomValuesModel
from pysatl_experiment.persistence.sqlalchemy.random_values import AlchemyRandomValuesStorage
from pysatl_experiment.sample_loading.sqlalchemy_source import StorageSampleSource
from pysatl_experiment.types import SampleSetSpec
from pysatl_experiment.utils.experiment_utils import get_sample_data_from_storage


class ExampleStatistic:
    def execute_statistic(self, rvs):
        return sum(rvs)


def test_execution_loads_only_requested_samples_of_its_experiment(tmp_path):
    connection = f"sqlite:///{tmp_path / 'samples.sqlite'}"
    storage = AlchemyRandomValuesStorage(connection)
    storage.init()
    storage.bulk_insert(
        RandomValuesModel(owner, code, {}, size, [float(i)] * size)
        for owner in ["other", "target"]
        for code in ["wrong", "generator"]
        for size in [1, 2]
        for i in range(5)
    )
    spec = CriticalValueTask(
        CriterionSpec("example", ExampleStatistic, {}),
        SampleSetSpec(experiment_name="target", generator_code="generator", sample_size=2, samples_count=3),
    )
    result = CriticalValueExecutionStep._execute_task(spec, StorageSampleSource(storage))
    assert result.worker_result.results_statistics == [0, 2, 4]
    assert get_sample_data_from_storage("generator", 2, 3, storage, "target") == [[0, 0], [1, 1], [2, 2]]
    spec = replace(spec, sample_set=replace(spec.sample_set, samples_count=6))
    with pytest.raises(ValueError, match="Not enough data"):
        CriticalValueExecutionStep._execute_task(spec, StorageSampleSource(storage))
    with pytest.raises(ValueError, match="Not enough data"):
        get_sample_data_from_storage("generator", 2, 6, storage, "target")
