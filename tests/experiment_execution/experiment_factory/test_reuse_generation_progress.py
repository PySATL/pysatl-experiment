"""Progress totals use the missing samples in a reused experiment's plan."""

from pysatl_experiment.experiment_execution.registry import create_default_experiment_registry
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState


def test_reuse_progress_counts_only_missing_samples(make_config, storages, capsys):
    config = make_config("time_complexity", "reuse")
    definition = create_default_experiment_registry(load_plugins=False).get("time_complexity")
    # Of 100 requested samples per size, 40 and 100 already exist.
    storages.data.count.side_effect = [40, 100]
    storages.result.get_data.return_value = None
    state = ExperimentRunState(config.experiment_name, False, False)
    plan = definition.task_planner(config, storages, state)
    steps = definition.factory().create_experiment_steps(config, storages, state, plan)

    assert steps.generation_step.total_samples == 60
    steps.generation_step.run()

    assert sum(len(call.args[0]) for call in storages.data.bulk_insert.call_args_list) == 60
    output = capsys.readouterr()
    assert "Generated: 60/60" in output.err
    assert "Saved: 60/60" in output.err
    assert "Generated:" not in output.out
