"""CriticalValue planning and assembly use explicitly prepared tasks."""

from pysatl_experiment.experiment_execution.registry import create_default_experiment_registry
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState
from pysatl_experiment.experiment_execution.step.execution_step.critical_value.critical_value_execution_step import (
    CriticalValueExecutionStep,
)


def test_missing_results_are_planned_then_passed_to_step(make_config, storages):
    config = make_config("critical_value")
    definition = create_default_experiment_registry(load_plugins=False).get("critical_value")
    storages.result.get_data.side_effect = [object()] + [None] * 1
    state = ExperimentRunState(config.experiment_name, False, False)
    plan = definition.task_planner(config, storages, state)
    assert len(plan.execution) == 1
    storages.result.reset_mock()
    steps = definition.factory().create_experiment_steps(config, storages, state, plan)
    assert isinstance(steps.execution_step, CriticalValueExecutionStep)
    assert steps.execution_step.context.tasks == tuple(plan.execution)
    assert steps.execution_step.experiment_name == state.experiment_name
    assert len(steps.execution_step._collect_tasks()) == 1
    assert steps.report_building_step.results_path == config.report.results_path
    assert steps.report_building_step.result_storage.storage is storages.result
    assert storages.result.mock_calls == []
