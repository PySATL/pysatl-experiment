"""Storage initialization, run preparation and assembly have separate effects."""

import importlib
from dataclasses import replace
from unittest.mock import Mock, call

import pytest

from pysatl_experiment.experiment_execution.experiment_config_adapter import ExperimentConfigAdapter
from pysatl_experiment.experiment_execution.planning.plan import ExperimentTaskPlan
from pysatl_experiment.experiment_execution.run_preparation import prepare_experiment
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState
from pysatl_experiment.types import RunMode


@pytest.mark.parametrize("run_mode", [RunMode.REUSE, RunMode.OVERWRITE])
def test_storage_creation_only_initializes_stores(config, definition, monkeypatch, run_mode):
    config = replace(config, run_mode=run_mode)
    module = importlib.import_module(definition.factory.__module__)
    base = importlib.import_module(
        "pysatl_experiment.experiment_execution.experiment_factory.abstract_experiment_factory"
    )
    result_class = {
        "critical_value": "AlchemyLimitDistributionStorage",
        "power": "AlchemyPowerStorage",
        "time_complexity": "AlchemyTimeComplexityStorage",
    }[config.experiment_type]
    constructors = [Mock(), Mock(), Mock()]
    monkeypatch.setattr(base, "AlchemyRandomValuesStorage", constructors[0])
    monkeypatch.setattr(module, result_class, constructors[1])
    monkeypatch.setattr(base, "AlchemyExperimentStorage", constructors[2])
    stores = definition.factory().create_storages(config)
    assert (stores.data, stores.result, stores.experiment) == tuple(c.return_value for c in constructors)
    for constructor in constructors:
        constructor.assert_called_once_with(config.storage_connection)
        assert constructor.return_value.mock_calls == [call.init()]
    assert not config.report.results_path.exists()


@pytest.mark.parametrize("run_mode", [RunMode.REUSE, RunMode.OVERWRITE])
def test_assembly_never_accesses_run_data(config, definition, storages, run_mode):
    config = replace(config, run_mode=run_mode)
    state = ExperimentRunState(experiment_name=config.experiment_name, generation_done=False, execution_done=False)
    # Empty lists still produce steps so the runner can mark them completed.
    steps = definition.factory().create_experiment_steps(config, storages, state, ExperimentTaskPlan([], []))
    assert steps.experiment_name == config.experiment_name
    assert steps.execution_step.experiment_name == config.experiment_name
    assert steps.generation_step is not None
    assert steps.report_building_step.result_storage.storage is storages.result
    assert storages.data.mock_calls == []
    assert storages.result.mock_calls == []
    assert storages.experiment.mock_calls == []
    assert not config.report.results_path.exists()


def test_assembly_passes_write_batch_size_to_execution(config, definition, storages):
    config = replace(config, execute=replace(config.execute, write_batch_size=7))
    state = ExperimentRunState(config.experiment_name, True, False)
    steps = definition.factory().create_experiment_steps(config, storages, state, ExperimentTaskPlan(None, []))
    assert steps.execution_step.write_batch_size == 7


@pytest.mark.parametrize(("generation_done", "execution_done"), [(True, False), (False, True), (True, True)])
def test_completed_steps_are_skipped_without_querying_their_data(
    config, definition, storages, generation_done, execution_done
):
    state = ExperimentRunState(config.experiment_name, generation_done, execution_done)
    plan = definition.task_planner(config, storages, state)
    steps = definition.factory().create_experiment_steps(config, storages, state, plan)
    assert (steps.generation_step is None) == generation_done
    assert (steps.execution_step is None) == execution_done
    assert steps.report_building_step is not None
    if generation_done:
        storages.data.count.assert_not_called()
    if execution_done:
        storages.result.get_data.assert_not_called()


def test_reuse_recovers_progress_without_mutating_stores(config, storages):
    storages.experiment.get_data.return_value = Mock(is_generation_done=True, is_execution_done=False)
    state = prepare_experiment(config, storages)
    assert state == ExperimentRunState(config.experiment_name, True, False)
    storages.experiment.insert_data.assert_not_called()
    assert storages.data.mock_calls == []
    assert storages.result.mock_calls == []
    assert config.report.results_path.is_dir()


def test_new_run_is_registered_with_unfinished_steps(config, storages):
    state = prepare_experiment(config, storages)
    model = storages.experiment.insert_data.call_args.args[0]
    assert state == ExperimentRunState(config.experiment_name, False, False)
    assert not model.is_generation_done
    assert not model.is_execution_done
    assert not model.is_report_building_done
    assert storages.data.mock_calls == []
    assert storages.result.mock_calls == []


def test_overwrite_resets_status_and_clears_only_configured_data_before_planning(config, definition, storages):
    config = replace(config, run_mode=RunMode.OVERWRITE)
    storages.experiment.get_data.return_value = Mock(is_generation_done=True, is_execution_done=True)
    state = prepare_experiment(config, storages)
    assert state == ExperimentRunState(config.experiment_name, False, False)
    model = storages.experiment.insert_data.call_args.args[0]
    assert not model.is_generation_done and not model.is_execution_done and not model.is_report_building_done
    sample_queries = [c.args[0] for c in storages.data.delete.call_args_list]
    assert {q.sample_size for q in sample_queries} == {10, 20}
    assert all(q.experiment_name == config.experiment_name for q in sample_queries)
    assert storages.result.delete_data.call_args_list == [
        call(query) for query in ExperimentConfigAdapter(config).result_queries()
    ]
    # The plan queries exactly the results which preparation invalidated.
    plan = definition.task_planner(config, storages, state)
    assert storages.result.get_data.call_args_list == storages.result.delete_data.call_args_list
    assert sum(task.samples_count for task in plan.generation) == 200
    assert len(plan.execution) == (4 if config.experiment_type == "power" else 2)


def test_planner_queries_only_missing_samples_and_does_not_write(config, definition, storages):
    storages.data.count.side_effect = [100, 97]
    plan = definition.task_planner(config, storages, ExperimentRunState(config.experiment_name, False, False))
    assert {task.sample_size for task in plan.generation} == {20}
    assert sum(task.samples_count for task in plan.generation) == 3
    assert all(c[0] == "count" for c in storages.data.mock_calls)
    assert all(c[0] == "get_data" for c in storages.result.mock_calls)
    assert storages.experiment.mock_calls == []
