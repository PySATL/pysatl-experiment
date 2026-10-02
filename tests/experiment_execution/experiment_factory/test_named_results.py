"""Workers and reports keep results attached to the experiment name."""

from types import SimpleNamespace
from unittest.mock import Mock

from pysatl_experiment.experiment_execution.planning.plan import ExperimentTaskPlan
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState
from pysatl_experiment.experiment_execution.step.execution_step.parallel_execution_step import ExecutionTaskResult


def test_worker_result_conversion_uses_experiment_name(config, definition, storages):
    state = ExperimentRunState(config.experiment_name, False, False)
    plan = definition.task_planner(config, storages, state)
    steps = definition.factory().create_experiment_steps(config, storages, state, plan)
    spec = steps.execution_step._collect_tasks()[0]
    result = SimpleNamespace(results_statistics=[0.1], results_times=[0.2], results_criteria=[True])
    model = steps.execution_step._to_model(ExecutionTaskResult(spec=spec, worker_result=result))
    assert model.experiment_name == config.experiment_name


def test_critical_value_report_reads_named_result(make_config, storages):
    from pysatl_experiment.experiment_execution.registry import create_default_experiment_registry

    config = make_config("critical_value")
    definition = create_default_experiment_registry(load_plugins=False).get("critical_value")
    state = ExperimentRunState(config.experiment_name, False, False)
    steps = definition.factory().create_experiment_steps(config, storages, state, ExperimentTaskPlan(None, None))
    storages.result.get_data.return_value = SimpleNamespace(results_statistics=[0.1, 0.2, 0.3])
    builder = Mock()
    steps.report_building_step.report_builder = builder
    steps.report_building_step.run()
    assert storages.result.get_data.call_count == 2
    assert all(
        call.args[0].experiment_name == config.experiment_name for call in storages.result.get_data.call_args_list
    )
    builder.build.assert_called_once()
