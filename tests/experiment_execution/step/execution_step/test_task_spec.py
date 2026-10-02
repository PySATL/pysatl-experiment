"""Prepared execution tasks transfer criterion metadata and sample identity."""

import pickle

import pytest

from pysatl_experiment.experiment_execution.criterion_spec import CriterionSpec
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.task_spec import CriticalValueTask
from pysatl_experiment.experiment_execution.step.execution_step.power.task_spec import PowerTask
from pysatl_experiment.types import SampleSetSpec


class ExampleStatistic:
    pass


@pytest.mark.parametrize("kind", ["critical_value", "power"])
def test_prepared_task_pickle_roundtrip(kind):
    criterion = CriterionSpec("test", ExampleStatistic, {"scale": 2.0})
    samples = SampleSetSpec(experiment_name="experiment", generator_code="normal", sample_size=10, samples_count=20)
    task = (
        CriticalValueTask(criterion, samples)
        if kind == "critical_value"
        else PowerTask(criterion, samples, 0.05, {"mean": [0.0, 1.0]})
    )
    restored = pickle.loads(pickle.dumps(task))  # noqa: S301
    assert restored == task
    assert restored.criterion.implementation is ExampleStatistic
