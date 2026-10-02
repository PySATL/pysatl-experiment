"""Behavior of JSON loading, validation and the factory boundary."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from unittest.mock import Mock

import pytest

from pysatl_experiment.configuration.config_loader import read_raw_experiment_config
from pysatl_experiment.configuration import (
    CriticalValueExperimentConfig,
    PowerExperimentConfig,
    RawExperimentConfig,
    TimeComplexityExperimentConfig,
)
from pysatl_experiment.configuration.validation import (
    ConfigReadError,
    ConfigValidationError,
    ExperimentValidationSpec,
    create_config_validator,
    validate_experiment_config,
)
from pysatl_experiment.configuration.validation.config_schemas import CriticalValueSchema
from pysatl_experiment.configuration.validation.config_validator import build_critical_value_config
from pysatl_experiment.experiment_execution.registry import ExperimentConfigRegistry
from pysatl_experiment.types import RunMode


EXAMPLES = Path(__file__).resolve().parents[2] / "experiment_example" / "configs"


@pytest.fixture
def document():
    return json.loads((EXAMPLES / "critical_values/normal_critical_values.json").read_text())


@pytest.mark.parametrize(
    ("filename", "expected_class"),
    [
        ("critical_values/normal_critical_values.json", CriticalValueExperimentConfig),
        ("power/normal_power.json", PowerExperimentConfig),
        ("time_complexity/laplace_time_complexity.json", TimeComplexityExperimentConfig),
    ],
)
def test_load_and_prepare_examples(filename, expected_class):
    raw = read_raw_experiment_config(EXAMPLES / filename)
    original = raw.to_data()
    config = validate_experiment_config(raw)
    assert isinstance(config, expected_class)
    assert config.run_mode is RunMode.REUSE
    assert config.execute.parallel_workers == 1
    assert config.execute.write_batch_size == 20
    assert isinstance(config.execute.criteria[0].parameters, dict)
    assert raw.to_data() == original


@pytest.mark.parametrize("data", [None, [], 12, "text", True])
def test_invalid_root_reaches_validator(tmp_path, data):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data))
    raw = read_raw_experiment_config(path)
    assert raw.to_data() == data
    with pytest.raises(ConfigValidationError) as error:
        validate_experiment_config(raw)
    assert error.value.issues[0].path == ()
    assert error.value.issues[0].code == "object_required"


def test_syntax_error_has_location(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{\n "generate": }')
    with pytest.raises(ConfigReadError, match=r"broken.json:2:\d+: invalid JSON"):
        read_raw_experiment_config(path)


def test_raw_does_not_expose_mutable_document(document):
    raw = RawExperimentConfig(document)
    raw.generate["distributions"].clear()
    raw.to_data()["generate"].clear()
    assert raw.to_data() == document
    assert not raw.has_field("future")
    assert RawExperimentConfig(future=None).has_field("future")


def test_errors_are_collected_with_nested_paths(document):
    document["generate"]["sample_sizes"] = [2, "100"]
    document["execute"]["criteria"][0]["criterion_code"] = 17
    document["execute"]["criteria"][1]["parameters"] = []
    document["report"] = None
    with pytest.raises(ConfigValidationError) as error:
        validate_experiment_config(RawExperimentConfig(document))
    paths = {issue.path for issue in error.value.issues}
    assert ("generate", "sample_sizes", 0) in paths
    assert ("generate", "sample_sizes", 1) in paths
    assert ("execute", "criteria", 0, "criterion_code") in paths
    assert ("execute", "criteria", 1, "parameters") in paths
    assert ("report",) in paths
    assert "execute.criteria[1].parameters" in str(error.value)


@pytest.mark.parametrize("value", [None, True, "1", 0])
def test_missing_workers_default_but_invalid_values_do_not(document, value):
    assert validate_experiment_config(RawExperimentConfig(document)).execute.parallel_workers == 1
    document["execute"]["parallel_workers"] = value
    with pytest.raises(ConfigValidationError):
        validate_experiment_config(RawExperimentConfig(document))


def test_unknown_fields_survive_raw_and_fail_validation(document):
    document["generate"]["typo"] = None
    raw = RawExperimentConfig(document)
    assert raw.generate["typo"] is None
    with pytest.raises(ConfigValidationError) as error:
        validate_experiment_config(raw)
    assert error.value.issues[0].path == ("generate", "typo")


@pytest.mark.parametrize("value", [None, True, "2", 0, -1, 1.5])
def test_invalid_write_batch_size_has_configuration_error(document, value):
    document["execute"]["write_batch_size"] = value
    with pytest.raises(ConfigValidationError) as error:
        validate_experiment_config(RawExperimentConfig(document))
    assert ("execute", "write_batch_size") in {issue.path for issue in error.value.issues}


def test_explicit_write_batch_size_is_preserved(document):
    document["execute"]["write_batch_size"] = 7
    config = validate_experiment_config(RawExperimentConfig(document))
    assert config.execute.write_batch_size == 7


@pytest.mark.parametrize("kind", [None, [], {}, "unknown"])
def test_invalid_discriminator_has_configuration_error(document, kind):
    document["experiment_type"] = kind
    with pytest.raises(ConfigValidationError) as error:
        validate_experiment_config(RawExperimentConfig(document))
    assert error.value.issues[0].path == ("experiment_type",)


def test_domain_checks_collect_incompatible_criteria_and_sample_counts(document):
    document["execute"]["criteria"][0]["criterion_code"] = "unknown"
    document["generate"]["samples_count"] = 1
    with pytest.raises(ConfigValidationError) as error:
        validate_experiment_config(RawExperimentConfig(document))
    assert {issue.code for issue in error.value.issues} == {"criterion_incompatible", "insufficient_samples"}


def test_new_experiment_can_register_schema_and_builder(document):
    class CustomSchema(CriticalValueSchema):
        experiment_type: Literal["custom"]

    @dataclass(frozen=True, kw_only=True)
    class CustomConfig(CriticalValueExperimentConfig):
        experiment_type: str = field(default="custom", init=False)

    def build(schema):
        config = build_critical_value_config(schema)
        return CustomConfig(
            experiment_name=config.experiment_name,
            storage_connection=config.storage_connection,
            run_mode=config.run_mode,
            generate=config.generate,
            execute=config.execute,
            report=config.report,
        )

    validator = create_config_validator()
    validator.register("custom", ExperimentValidationSpec(CustomSchema, build))
    document["experiment_type"] = "custom"
    assert isinstance(validator.validate(RawExperimentConfig(document)), CustomConfig)


def test_invalid_config_never_checks_dependencies_or_calls_factory(tmp_path, document):
    from pysatl_experiment.experiment_execution import build as pipeline

    document["execute"]["criteria"] = None
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(document))
    dependencies = Mock()
    factory = Mock()
    registry = ExperimentConfigRegistry()
    registry.register(
        "critical_value",
        schema=CriticalValueSchema,
        config_builder=build_critical_value_config,
        factory=factory,
        run_preparer=Mock(),
        task_planner=Mock(),
        dependency_checker=dependencies,
    )
    with pytest.raises(ConfigValidationError):
        pipeline.build_experiment_from_json(path, registry=registry)
    dependencies.assert_not_called()
    factory.assert_not_called()


def test_pipeline_prepares_and_plans_before_assembly(tmp_path, document):
    from pysatl_experiment.experiment_execution import build as pipeline

    path = tmp_path / "valid.json"
    path.write_text(json.dumps(document))
    events = []
    storages, state, plan = object(), object(), object()
    factory = Mock()
    factory.create_storages.side_effect = lambda config: events.append("stores") or storages
    factory.create_experiment_steps.side_effect = lambda *args: events.append("assemble") or "steps"
    prepare = Mock(side_effect=lambda *args: events.append("prepare") or state)
    planner = Mock(side_effect=lambda *args: events.append("plan") or plan)
    registry = ExperimentConfigRegistry()
    registry.register(
        "critical_value",
        schema=CriticalValueSchema,
        config_builder=build_critical_value_config,
        factory=lambda: factory,
        run_preparer=prepare,
        task_planner=planner,
        dependency_checker=lambda config: events.append("check"),
    )
    assert pipeline.build_experiment_from_json(path, registry=registry) == "steps"
    assert events == ["check", "stores", "prepare", "plan", "assemble"]
    config = factory.create_storages.call_args.args[0]
    assert isinstance(config, CriticalValueExperimentConfig)
    prepare.assert_called_once_with(config, storages)
    planner.assert_called_once_with(config, storages, state)
    factory.create_experiment_steps.assert_called_once_with(config, storages, state, plan)


@pytest.mark.parametrize(
    "filename",
    [
        "critical_values/normal_critical_values.json",
        "power/normal_power.json",
        "time_complexity/laplace_time_complexity.json",
    ],
)
def test_real_factories_accept_new_config(tmp_path, filename):
    from pysatl_experiment.experiment_execution.build import get_experiment_factory

    document = read_raw_experiment_config(EXAMPLES / filename).to_dict()
    document["storage_connection"] = f"sqlite:///{tmp_path / 'experiment.sqlite'}"
    document["generate"]["parallel_workers"] = 2
    document["execute"]["parallel_workers"] = 3
    results_path = tmp_path / "custom" / "reports"
    document["report"]["results_path"] = str(results_path)
    config = validate_experiment_config(RawExperimentConfig(document))
    assert not results_path.exists()
    factory = get_experiment_factory(config.experiment_type)
    from pysatl_experiment.experiment_execution.registry import create_default_experiment_registry

    definition = create_default_experiment_registry(load_plugins=False).get(config.experiment_type)
    storages = factory.create_storages(config)
    assert not results_path.exists()
    state = definition.run_preparer(config, storages)
    plan = definition.task_planner(config, storages, state)
    steps = factory.create_experiment_steps(config, storages, state, plan)
    assert factory.config is config
    assert steps.experiment_name == config.experiment_name
    assert steps.generation_step.parallel_workers == 2
    assert steps.execution_step.parallel_workers == 3
    assert steps.report_building_step is not None
    assert steps.report_building_step.results_path == results_path
    assert results_path.is_dir()
    assert not hasattr(factory, "results_path")
    assert steps.execution_step._collect_tasks()


def test_power_dependency_error_is_separate_from_validation():
    from pysatl_experiment.experiment_execution.dependencies import (
        ExperimentDependencyError,
        check_experiment_dependencies,
    )

    config = validate_experiment_config(read_raw_experiment_config(EXAMPLES / "power/normal_power.json"))
    checker = Mock()
    checker.check_exists.return_value = False
    with pytest.raises(ExperimentDependencyError, match="Missing critical value distributions"):
        check_experiment_dependencies(config, checker)
    checker.check_exists.return_value = True
    check_experiment_dependencies(config, checker)


@pytest.mark.parametrize("kind", ["critical_value", "power", "time_complexity"])
def test_cli_create_configure_and_build_share_the_new_format(tmp_path, monkeypatch, kind):
    import importlib

    from click.testing import CliRunner

    from pysatl_experiment.cli.cli import cli
    from pysatl_experiment.utils import files_utils

    monkeypatch.setattr(files_utils, "USER_DATA_DIR", str(tmp_path))
    runner = CliRunner()
    created = runner.invoke(cli, ["create", "example"])
    assert created.exit_code == 0, created.output
    configured = runner.invoke(
        cli,
        [
            "configure",
            "example",
            "--connection",
            f"sqlite:///{tmp_path / 'run.sqlite'}",
            "--experiment-type",
            kind,
            "--hypothesis",
            "normal",
            "--size",
            "10",
            "--count",
            "100",
            "--criteria",
            "KS",
            "--levels",
            "0.05",
        ],
    )
    assert configured.exit_code == 0, configured.output
    raw = read_raw_experiment_config(files_utils.ensure_experiment_conf("example"))
    assert raw.experiment_type == kind
    assert not raw.has_field("config")
    assert validate_experiment_config(raw).execute.criteria[0].parameters == {}
    module = importlib.import_module("pysatl_experiment.cli.commands.build_and_run")
    build = Mock(return_value=Mock())
    experiment = Mock()
    monkeypatch.setattr(module, "build_experiment", build)
    monkeypatch.setattr(module, "Experiment", experiment)
    run = runner.invoke(cli, ["build-and-run", "example"])
    assert run.exit_code == 0, run.output
    assert build.call_args.args[0].experiment_type == kind
    experiment.return_value.run_experiment.assert_called_once()


def test_generation_keeps_random_parameter_ranges(document):
    from pysatl_experiment.experiment_execution.planning.generation import plan_generation

    document["generate"]["distributions"][0]["distribution_params"]["mean"] = [-2, 2]
    document["generate"]["samples_count"] = 100
    document["generate"]["sample_sizes"] = [10]
    document["execute"]["monte_carlo_count"] = 100
    config = validate_experiment_config(RawExperimentConfig(document))
    storage = Mock()
    storage.count.return_value = 97
    tasks = plan_generation(config, storage)
    assert len(tasks) == 3
    for task in tasks:
        assert task.samples_count == 1
        assert -2 <= task.generator.parameters()["mean"] <= 2
    assert config.generate.distributions[0].distribution_params["mean"] == [-2, 2]


@pytest.mark.parametrize("parameter_range", [[2, -2], [1], [1, 2, 3]])
def test_invalid_distribution_ranges_are_reported(document, parameter_range):
    document["generate"]["distributions"][0]["distribution_params"]["mean"] = parameter_range
    with pytest.raises(ConfigValidationError) as error:
        validate_experiment_config(RawExperimentConfig(document))
    assert all(issue.path[:3] == ("generate", "distributions", 0) for issue in error.value.issues)


def test_default_report_path_is_prepared_without_creating_directory(document, tmp_path, monkeypatch):
    from pysatl_experiment.constants import RESULTS_DIR, USER_DATA_DIR

    monkeypatch.chdir(tmp_path)
    document["report"].pop("results_path", None)
    raw = RawExperimentConfig(document)
    config = validate_experiment_config(raw)
    assert config.report.results_path == tmp_path / USER_DATA_DIR / RESULTS_DIR
    assert not config.report.results_path.exists()
    assert "results_path" not in raw.report


def test_relative_report_path_is_resolved_from_working_directory(document, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    document["report"]["results_path"] = "reports/normal"
    raw = RawExperimentConfig(document)
    config = validate_experiment_config(raw)
    assert config.report.results_path == tmp_path / "reports" / "normal"
    assert not config.report.results_path.exists()
    assert raw.report["results_path"] == "reports/normal"


@pytest.mark.parametrize("results_path", [None, "", "  ", "bad\x00path", 12, [], {}])
def test_invalid_report_path_has_field_error(document, results_path):
    document["report"]["results_path"] = results_path
    with pytest.raises(ConfigValidationError) as error:
        validate_experiment_config(RawExperimentConfig(document))
    assert error.value.issues[0].path == ("report", "results_path")


@pytest.mark.parametrize("failed_stage", ["create_storages", "prepare", "plan"])
def test_pipeline_stops_after_failed_stage(document, failed_stage):
    from pysatl_experiment.experiment_execution.build import build_experiment

    config = validate_experiment_config(RawExperimentConfig(document))
    factory = Mock()
    prepare, planner = Mock(), Mock()
    stages = {"create_storages": factory.create_storages, "prepare": prepare, "plan": planner}
    stages[failed_stage].side_effect = RuntimeError("stage failed")
    registry = ExperimentConfigRegistry()
    registry.register(
        "critical_value",
        schema=CriticalValueSchema,
        config_builder=build_critical_value_config,
        factory=lambda: factory,
        run_preparer=prepare,
        task_planner=planner,
    )
    with pytest.raises(RuntimeError, match="stage failed"):
        build_experiment(config, registry=registry)
    factory.create_experiment_steps.assert_not_called()
    if failed_stage != "plan":
        planner.assert_not_called()
    if failed_stage == "create_storages":
        prepare.assert_not_called()
