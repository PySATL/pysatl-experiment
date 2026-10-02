"""TimeComplexity planning and assembly use explicitly prepared tasks."""

import pytest

from pysatl_experiment.experiment_execution.registry import create_default_experiment_registry
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState
from pysatl_experiment.experiment_execution.step.execution_step.time_complexity.time_complexity_execution_step import (
    TimeComplexityExecutionStep,
)


def test_missing_results_are_planned_then_passed_to_step(make_config, storages):
    config = make_config("time_complexity")
    definition = create_default_experiment_registry(load_plugins=False).get("time_complexity")
    storages.result.get_data.side_effect = [object()] + [None] * 1
    state = ExperimentRunState(config.experiment_name, False, False)
    plan = definition.task_planner(config, storages, state)
    assert len(plan.execution) == 1
    storages.result.reset_mock()
    steps = definition.factory().create_experiment_steps(config, storages, state, plan)
    assert isinstance(steps.execution_step, TimeComplexityExecutionStep)
    assert steps.execution_step.context.tasks == tuple(plan.execution)
    assert steps.execution_step.experiment_name == state.experiment_name
    assert len(steps.execution_step._collect_tasks()) == 1
    assert steps.report_building_step.results_path == config.report.results_path
    assert steps.report_building_step.result_storage.storage is storages.result
    assert storages.result.mock_calls == []


@pytest.mark.parametrize("run_mode", ["reuse", "overwrite"])
def test_real_storage_progress_and_data_follow_run_mode(make_config, run_mode):
    from dataclasses import asdict, replace

    from pysatl_experiment.experiment_execution.experiment_config_adapter import ExperimentConfigAdapter
    from pysatl_experiment.experiment_execution.run_preparation import experiment_query
    from pysatl_experiment.persistence.models.random_values import RandomValuesFilter, RandomValuesModel
    from pysatl_experiment.persistence.models.time_complexity import TimeComplexityModel

    config = make_config("time_complexity", run_mode)
    definition = create_default_experiment_registry(load_plugins=False).get("time_complexity")
    factory = definition.factory()
    storages = factory.create_storages(config)
    state = definition.run_preparer(config, storages)
    storages.experiment.set_generation_done(state.experiment_name)
    storages.experiment.set_execution_done(state.experiment_name)
    storages.experiment.set_report_building_done(state.experiment_name)
    generator_code, _, generator = ExperimentConfigAdapter(config).generator_metadata()[0]
    sample_query = RandomValuesFilter(
        generator_code=generator_code,
        experiment_name=config.experiment_name,
        sample_size=10,
    )
    storages.data.bulk_insert(
        [RandomValuesModel(**asdict(sample_query), generator_parameters=generator.parameters(), data=[0.0] * 10)]
    )
    result_query = next(ExperimentConfigAdapter(config).result_queries())
    storages.result.insert_data(TimeComplexityModel(**asdict(result_query), results_times=[0.1]))
    other_sample_query = replace(sample_query, experiment_name="another_experiment")
    other_result_query = replace(result_query, experiment_name="another_experiment")
    storages.data.bulk_insert(
        [RandomValuesModel(**asdict(other_sample_query), generator_parameters=generator.parameters(), data=[1.0] * 10)]
    )
    storages.result.insert_data(TimeComplexityModel(**asdict(other_result_query), results_times=[0.2]))

    restored = definition.run_preparer(config, storages)
    saved = storages.experiment.get_data(experiment_query(config))
    reused = run_mode == "reuse"
    assert restored == ExperimentRunState(state.experiment_name, reused, reused)
    assert saved.is_generation_done == reused
    assert saved.is_execution_done == reused
    assert saved.is_report_building_done == reused
    assert storages.data.count(sample_query) == int(reused)
    assert (storages.result.get_data(result_query) is not None) == reused
    assert storages.data.count(other_sample_query) == 1
    assert storages.result.get_data(other_result_query) is not None
    plan = definition.task_planner(config, storages, restored)
    assert (plan.generation is None) == reused
    assert (plan.execution is None) == reused


def test_planning_resolves_class_and_merges_parameters_without_constructing_statistic(
    make_config, storages, monkeypatch
):
    from dataclasses import replace

    from pysatl_experiment.configuration import CriterionConfig
    from pysatl_experiment.experiment_execution import experiment_config_adapter
    from pysatl_experiment.experiment_execution.planning.time_complexity import plan_time_complexity_tasks

    class UnconstructedStatistic:
        def __init__(self, **parameters):
            raise AssertionError("Planning must not construct a statistic")

        @classmethod
        def short_code(cls):
            return "TEST"

        @classmethod
        def code(cls):
            return "test_statistic"

    config = make_config("time_complexity")
    config = replace(
        config,
        execute=replace(
            config.execute,
            hypothesis_params={"location": 2.0, "scale": 1.0},
            criteria=[CriterionConfig(criterion_code="TEST", parameters={"scale": 3.0})],
        ),
    )
    monkeypatch.setattr(experiment_config_adapter, "get_available_criteria", lambda _: [UnconstructedStatistic])
    plan = plan_time_complexity_tasks(config, storages, ExperimentRunState(config.experiment_name, True, False))
    assert len(plan.execution) == 2
    for task in plan.execution:
        assert task.criterion.implementation is UnconstructedStatistic
        assert task.criterion.parameters == {"location": 2.0, "scale": 3.0}
        assert task.sample_set.samples_count == config.execute.monte_carlo_count
    assert all(
        call.args[0].criterion_parameters == {"location": 2.0, "scale": 3.0}
        for call in storages.result.get_data.call_args_list
    )
    definition = create_default_experiment_registry(load_plugins=False).get("time_complexity")
    steps = definition.factory().create_experiment_steps(
        config, storages, ExperimentRunState(config.experiment_name, True, False), plan
    )
    assert len(steps.report_building_step.result_storage.queries) == 2
    assert all(
        query.criterion_parameters == {"location": 2.0, "scale": 3.0}
        for query in steps.report_building_step.result_storage.queries
    )
