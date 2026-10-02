"""Configured sample series survive generation, execution, reuse and overwrite."""

from dataclasses import asdict, replace
from unittest.mock import Mock

import pytest

from pysatl_experiment.configuration import DistributionConfig
from pysatl_experiment.experiment_execution.experiment_config_adapter import ExperimentConfigAdapter
from pysatl_experiment.experiment_execution.planning import generation
from pysatl_experiment.experiment_execution.registry import create_default_experiment_registry
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState
from pysatl_experiment.experiment_execution.step.report_step.time_complexity.time_complexity_report_builder import (
    TimeComplexityReportBuilder,
)
from pysatl_experiment.persistence.models.random_values import RandomValuesFilter, RandomValuesModel
from pysatl_experiment.persistence.models.time_complexity import TimeComplexityFilter, TimeComplexityModel
from pysatl_experiment.sample_loading.loading import load_sample_batch
from pysatl_experiment.types import RunMode


@pytest.fixture
def series_config(make_config):
    config = make_config("time_complexity")
    distributions = [
        DistributionConfig(distribution_type="normal", distribution_params={"mean": [0.0, 2.0]}),
        DistributionConfig(distribution_type="normal", distribution_params={"mean": [0.5, 1.5]}),
        DistributionConfig(distribution_type="normal", distribution_params={"mean": 1.0}),
        DistributionConfig(distribution_type="laplace", distribution_params={"t": 0.0, "s": 1.0}),
    ]
    return replace(
        config,
        generate=replace(config.generate, distributions=distributions, sample_sizes=[10], samples_count=3),
        execute=replace(config.execute, monte_carlo_count=3),
    )


def test_series_remain_separate_through_execution_reuse_and_overwrite(series_config, monkeypatch):
    # Equal realized means must not merge fixed and overlapping ranged series.
    monkeypatch.setattr(generation.random, "uniform", lambda lower, upper: (lower + upper) / 2)
    config = series_config
    definition = create_default_experiment_registry(load_plugins=False).get("time_complexity")
    factory = definition.factory()
    storages = factory.create_storages(config)
    state = definition.run_preparer(config, storages)
    plan = definition.task_planner(config, storages, state)
    codes = {
        "normal_mean_[0.0,2.0]_var_1.0",
        "normal_mean_[0.5,1.5]_var_1.0",
        "normal_mean_1.0_var_1.0",
        "laplace_s_1.0_t_0.0",
    }
    assert {task.sample_set.generator_code for task in plan.execution} == codes
    assert sum(task.samples_count for task in plan.generation) == 12
    steps = factory.create_experiment_steps(config, storages, state, plan)
    steps.generation_step.run()

    for task in plan.execution:
        spec = task.sample_set
        assert len(load_sample_batch(storages.data, spec).samples) == 3
        query = RandomValuesFilter(experiment_name=config.experiment_name, generator_code=spec.generator_code)
        rows = storages.data.read_bulk(query).items
        assert len(rows) == 3
        if spec.generator_code.startswith("normal_"):
            assert all(row.generator_parameters == {"mean": 1.0, "var": 1.0} for row in rows)

    steps.execution_step.run()
    results = storages.result.read_bulk(TimeComplexityFilter(experiment_name=config.experiment_name)).items
    assert {row.generator_code for row in results} == codes
    assert len(results) == 4
    assert all(len(row.results_times) == 3 for row in results)
    report_builder = Mock()
    steps.report_building_step.report_builder = report_builder
    steps.report_building_step.run()
    report_context = report_builder.build.call_args.args[0]
    report = TimeComplexityReportBuilder()._collect_statistics(report_context.data).as_dict()
    assert {series.generator_code for series in report} == codes
    assert all(len(points) == 1 and points[0][0] == 10 for points in report.values())

    replanned = definition.task_planner(config, storages, state)
    assert replanned.generation == []
    assert replanned.execution == []

    queries = list(ExperimentConfigAdapter(config).result_queries())
    storages.result.delete_data(queries[0])
    pending = definition.task_planner(config, storages, state)
    assert [task.sample_set.generator_code for task in pending.execution] == [queries[0].generator_code]

    other_sample = RandomValuesModel("other", queries[0].generator_code, {"mean": 1.0, "var": 1.0}, 10, [0.0] * 10)
    storages.data.bulk_insert([other_sample])
    other_result = TimeComplexityModel(**asdict(replace(queries[0], experiment_name="other")), results_times=[0.1] * 3)
    storages.result.bulk_insert([other_result])
    reset = definition.run_preparer(replace(config, run_mode=RunMode.OVERWRITE), storages)
    assert reset == ExperimentRunState(config.experiment_name, False, False)
    assert storages.data.count(RandomValuesFilter(experiment_name=config.experiment_name)) == 0
    assert storages.result.read_bulk(TimeComplexityFilter(experiment_name=config.experiment_name)).items == []
    assert storages.data.read_bulk(RandomValuesFilter(experiment_name="other")).items == [other_sample]
    assert storages.result.read_bulk(TimeComplexityFilter(experiment_name="other")).items == [other_result]


def test_ranges_are_sampled_once_per_missing_sample(series_config, monkeypatch):
    config = replace(
        series_config,
        generate=replace(series_config.generate, distributions=series_config.generate.distributions[:1]),
    )
    uniform = Mock(side_effect=[0.25, 0.5, 1.75])
    monkeypatch.setattr(generation.random, "uniform", uniform)
    storage = Mock()
    storage.count.return_value = 0
    tasks = generation.plan_generation(config, storage)
    assert [task.generator.parameters()["mean"] for task in tasks] == [0.25, 0.5, 1.75]
    assert [task.samples_count for task in tasks] == [1, 1, 1]
    assert {task.generator_code for task in tasks} == {"normal_mean_[0.0,2.0]_var_1.0"}
    assert [call.args for call in uniform.call_args_list] == [(0.0, 2.0)] * 3
    storage.count.return_value = 3
    assert generation.plan_generation(config, storage) == []
    assert uniform.call_count == 3


def test_defaults_and_explicit_parameters_identify_the_same_series(series_config):
    codes = []
    for parameters in ({}, {"var": 1, "mean": -0.0}):
        config = replace(
            series_config,
            generate=replace(
                series_config.generate,
                distributions=[DistributionConfig(distribution_type="normal", distribution_params=parameters)],
            ),
        )
        codes.append(ExperimentConfigAdapter(config).generator_metadata()[0][0])
    assert codes == ["normal_mean_0.0_var_1.0"] * 2
