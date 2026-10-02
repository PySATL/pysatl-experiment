"""Planning resolves metadata without constructing live statistics."""

from dataclasses import replace

import pytest

from pysatl_experiment.configuration import CriterionConfig
from pysatl_experiment.experiment_execution import experiment_config_adapter
from pysatl_experiment.experiment_execution.registry import create_default_experiment_registry
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState


class MetadataOnlyStatistic:
    def __init__(self, **parameters):
        raise AssertionError("Planning must not construct statistics")

    @classmethod
    def short_code(cls):
        return "TEST"

    @classmethod
    def code(cls):
        return "test_statistic"


@pytest.mark.parametrize("kind", ["critical_value", "power"])
def test_planner_and_report_queries_share_full_parameters(kind, make_config, storages, monkeypatch):
    config = make_config(kind)
    config = replace(
        config,
        execute=replace(
            config.execute,
            hypothesis_params={"location": 2.0, "scale": 1.0},
            criteria=[CriterionConfig(criterion_code="TEST", parameters={"scale": 3.0})],
        ),
    )
    monkeypatch.setattr(experiment_config_adapter, "get_available_criteria", lambda _: [MetadataOnlyStatistic])
    definition = create_default_experiment_registry(load_plugins=False).get(kind)
    # Generation is already complete, execution must still plan every missing result.
    storages.result.get_data.return_value = None
    plan = definition.task_planner(config, storages, ExperimentRunState(config.experiment_name, True, False))
    assert len(plan.execution) == (2 if kind == "critical_value" else 4)
    expected = {"location": 2.0, "scale": 3.0}
    assert all(task.criterion.parameters == expected for task in plan.execution)
    assert all(task.criterion.implementation is MetadataOnlyStatistic for task in plan.execution)
    assert all(task.sample_set.samples_count == 100 for task in plan.execution)
    queries = [call.args[0] for call in storages.result.get_data.call_args_list]
    assert all(query.criterion_parameters == expected for query in queries)
    assert queries == list(experiment_config_adapter.ExperimentConfigAdapter(config).result_queries())
    storages.result.get_data.side_effect = [object()] * len(queries)
    reused = definition.task_planner(config, storages, ExperimentRunState(config.experiment_name, True, False))
    assert reused.execution == []


def test_report_criterion_metadata_includes_hypothesis_parameters_without_mutating_config(make_config, monkeypatch):
    class ConfiguredStatistic(MetadataOnlyStatistic):
        def __init__(self, **parameters):
            self.parameters = parameters

    config = make_config("critical_value")
    config = replace(
        config,
        execute=replace(
            config.execute,
            hypothesis_params={"location": 2.0, "scale": 1.0},
            criteria=[CriterionConfig(criterion_code="TEST", parameters={"scale": 3.0})],
        ),
    )
    monkeypatch.setattr(experiment_config_adapter, "get_available_criteria", lambda _: [ConfiguredStatistic])
    resolved = experiment_config_adapter.ExperimentConfigAdapter(config).criteria_config()[0]
    assert resolved.criterion.parameters == {"location": 2.0, "scale": 3.0}
    assert resolved.statistics_class_object.parameters == resolved.criterion.parameters
    assert config.execute.criteria[0].parameters == {"scale": 3.0}
