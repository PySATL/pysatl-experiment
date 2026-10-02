"""Experiment names isolate progress and results with identical configurations."""

from dataclasses import replace
from unittest.mock import Mock

import pytest

from pysatl_experiment.experiment_execution.experiment_steps import ExperimentSteps
from pysatl_experiment.experiment_execution.runner import Experiment
from pysatl_experiment.persistence.models.experiment import ExperimentModel, ExperimentQuery
from pysatl_experiment.persistence.models.limit_distribution import LimitDistributionModel, LimitDistributionQuery
from pysatl_experiment.persistence.models.power import PowerModel, PowerQuery
from pysatl_experiment.persistence.sqlalchemy.experiment import AlchemyExperimentStorage
from pysatl_experiment.persistence.sqlalchemy.limit_distribution import AlchemyLimitDistributionStorage
from pysatl_experiment.persistence.sqlalchemy.power import AlchemyPowerStorage


def experiment(name):
    return ExperimentModel(
        experiment_name=name,
        experiment_type="time_complexity",
        storage_connection="sqlite://",
        run_mode="reuse",
        report_mode="without-chart",
        hypothesis="normal",
        generator_type="standard",
        executor_type="standard",
        report_builder_type="standard",
        sample_sizes=[10],
        monte_carlo_count=100,
        criteria={},
        alternatives={},
        significance_levels=[0.05],
        parallel_workers=1,
        is_generation_done=False,
        is_execution_done=False,
        is_report_building_done=False,
    )


def test_name_is_the_only_experiment_key(tmp_path):
    storage = AlchemyExperimentStorage(f"sqlite:///{tmp_path / 'experiment.db'}")
    storage.init()
    storage.insert_data(experiment("first"))
    storage.insert_data(experiment("second"))
    storage.set_generation_done("first")
    storage.set_execution_done("first")
    storage.set_report_building_done("first")
    first = storage.get_data(ExperimentQuery("first"))
    second = storage.get_data(ExperimentQuery("second"))
    assert first.is_generation_done and first.is_execution_done and first.is_report_building_done
    assert second == experiment("second")
    changed = replace(first, monte_carlo_count=200)
    storage.insert_data(changed)
    assert storage.get_data(ExperimentQuery("first")) == changed
    storage.delete_data(ExperimentQuery("first"))
    assert storage.get_data(ExperimentQuery("first")) is None
    assert storage.get_data(ExperimentQuery("second")) == second
    with pytest.raises(ValueError, match="not found"):
        storage.set_generation_done("missing")


@pytest.mark.parametrize("kind", ["power", "critical_value"])
def test_results_are_isolated_by_name(tmp_path, kind):
    common = dict(
        experiment_name="first", criterion_code="KS", criterion_parameters={}, sample_size=10, monte_carlo_count=100
    )
    if kind == "power":
        common.update(alternative_code="normal", alternative_parameters={}, significance_level=0.05)
        model = PowerModel(**common, results_criteria=[True])
        query = PowerQuery(**common)
        storage = AlchemyPowerStorage(f"sqlite:///{tmp_path / 'results.db'}")
    else:
        model = LimitDistributionModel(**common, results_statistics=[0.1])
        query = LimitDistributionQuery(**common)
        storage = AlchemyLimitDistributionStorage(f"sqlite:///{tmp_path / 'results.db'}")
    storage.init()
    other = replace(model, experiment_name="second")
    storage.bulk_insert_data([model, other])
    assert storage.get_data(query) == model
    assert storage.get_data(replace(query, experiment_name="second")) == other
    storage.delete_data(query)
    assert storage.get_data(query) is None
    assert storage.get_data(replace(query, experiment_name="second")) == other


def test_runner_updates_statuses_by_name():
    storage = Mock()
    steps = ExperimentSteps("named", storage, Mock(), Mock(), Mock())
    Experiment(steps).run_experiment()
    storage.set_generation_done.assert_called_once_with("named")
    storage.set_execution_done.assert_called_once_with("named")
    storage.set_report_building_done.assert_called_once_with("named")
