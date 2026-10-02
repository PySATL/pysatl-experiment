"""External experiment registration and installed plugin discovery."""

import json
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Literal
from unittest.mock import Mock

import pytest
from click.testing import CliRunner
from pydantic import BaseModel, ConfigDict, Field

from pysatl_experiment.configuration import (
    ExecutionConfig,
    ExperimentConfig,
    GenerationConfig,
    RawExperimentConfig,
    ReportConfig,
)
from pysatl_experiment.configuration.validation import ConfigIssue, ConfigValidationError, validate_experiment_config
from pysatl_experiment.experiment_execution.build import build_experiment, build_experiment_from_json
from pysatl_experiment.experiment_execution.dependencies import ExperimentDependencyError
from pysatl_experiment.experiment_execution.experiment_steps import ExperimentSteps
from pysatl_experiment.experiment_execution.registry import (
    EXPERIMENT_ENTRY_POINT_GROUP,
    ExperimentConfigRegistry,
    ExperimentPluginError,
    ExperimentRegistryError,
    create_default_experiment_registry,
)
from pysatl_experiment.types import ReportMode, RunMode, StepType


class CustomSchema(BaseModel):
    """An external schema need not inherit any built-in statistical schema."""

    model_config = ConfigDict(extra="forbid")
    experiment_type: Literal["custom"]
    factor: int = Field(gt=0, strict=True)


@dataclass(frozen=True, kw_only=True)
class CustomConfig(ExperimentConfig[GenerationConfig, ReportConfig, ExecutionConfig]):
    experiment_type: str = field(default="custom", init=False)
    factor: int


def build_custom_config(schema: CustomSchema) -> CustomConfig:
    return CustomConfig(
        experiment_name="custom_example",
        storage_connection="sqlite://",
        run_mode=RunMode.REUSE,
        factor=schema.factor,
        generate=GenerationConfig(generator_type=StepType.STANDARD, parallel_workers=1, distributions=[]),
        report=ReportConfig(
            report_builder_type=StepType.STANDARD,
            report_mode=ReportMode.WITHOUT_CHART,
            results_path=Path("unused"),
        ),
        execute=ExecutionConfig(
            hypothesis="custom",
            hypothesis_params={},
            criteria=[],
            executor_type=StepType.STANDARD,
            monte_carlo_count=1,
            parallel_workers=1,
            significance_levels=[],
        ),
    )


@dataclass(frozen=True)
class CustomStores:
    experiment: Mock
    factor: int


@dataclass(frozen=True)
class CustomState:
    experiment_name: str


@dataclass(frozen=True)
class CustomPlan:
    jobs: tuple[int, ...]


class CustomFactory:
    """A standalone factory implementing the protocol without the built-in base class."""

    def create_storages(self, experiment_config: CustomConfig) -> CustomStores:
        return CustomStores(experiment=Mock(), factor=experiment_config.factor)

    def create_experiment_steps(
        self, experiment_config: CustomConfig, storages: CustomStores, state: CustomState, plan: CustomPlan
    ) -> ExperimentSteps:
        assert plan.jobs == (experiment_config.factor * 2,)
        return ExperimentSteps(
            experiment_name=f"custom_factor_{experiment_config.factor}",
            experiment_storage=storages.experiment,
            generation_step=None,
            execution_step=None,
            report_building_step=None,
        )


def prepare_custom_run(config: CustomConfig, storages: CustomStores) -> CustomState:
    assert storages.factor == config.factor
    return CustomState(experiment_name=f"custom_factor_{config.factor}")


def plan_custom_tasks(config: CustomConfig, storages: CustomStores, state: CustomState) -> CustomPlan:
    assert state.experiment_name == f"custom_factor_{storages.factor}"
    return CustomPlan(jobs=(config.factor * 2,))


def register_test_plugin(registry):
    registry.register(
        "custom",
        schema=CustomSchema,
        config_builder=build_custom_config,
        factory=CustomFactory,
        run_preparer=prepare_custom_run,
        task_planner=plan_custom_tasks,
    )


@pytest.fixture
def custom_json(tmp_path):
    path = tmp_path / "custom.json"
    path.write_text(json.dumps({"experiment_type": "custom", "factor": 7}))
    return path


@pytest.fixture
def installed_plugin(tmp_path, monkeypatch):
    """Provide real distribution metadata discoverable by importlib.metadata."""
    distribution = tmp_path / "pysatl_test_plugin-1.0.dist-info"
    distribution.mkdir()
    (distribution / "METADATA").write_text("Metadata-Version: 2.1\nName: pysatl-test-plugin\nVersion: 1.0\n")
    (distribution / "entry_points.txt").write_text(
        f"[{EXPERIMENT_ENTRY_POINT_GROUP}]\ncustom = {__name__}:register_test_plugin\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    return distribution


def test_register_custom_kind_and_build_from_json(custom_json):
    registry = create_default_experiment_registry(load_plugins=False)
    register_test_plugin(registry)
    result = build_experiment_from_json(custom_json, registry=registry)
    assert result.experiment_name == "custom_factor_7"


def test_registry_instances_are_isolated(custom_json):
    first = create_default_experiment_registry(load_plugins=False)
    second = create_default_experiment_registry(load_plugins=False)
    register_test_plugin(first)
    with pytest.raises(ConfigValidationError) as error:
        build_experiment_from_json(custom_json, registry=second)
    assert error.value.issues[0].path == ("experiment_type",)


def test_duplicate_registration_cannot_replace_builtin():
    registry = create_default_experiment_registry(load_plugins=False)
    original = registry.get("power")
    with pytest.raises(ExperimentRegistryError, match="already registered: power"):
        registry.register(
            "power",
            schema=CustomSchema,
            config_builder=build_custom_config,
            factory=CustomFactory,
            run_preparer=prepare_custom_run,
            task_planner=plan_custom_tasks,
        )
    assert registry.get("power") is original


def test_unknown_factory_has_registry_error():
    registry = ExperimentConfigRegistry()
    config = build_custom_config(CustomSchema(experiment_type="custom", factor=2))
    with pytest.raises(ExperimentRegistryError, match="Unsupported experiment type: custom"):
        build_experiment(config, registry=registry)


def test_custom_domain_errors_stop_builder_and_factory(custom_json):
    builder = Mock(wraps=build_custom_config)
    factory = Mock()
    registry = ExperimentConfigRegistry()
    registry.register(
        "custom",
        schema=CustomSchema,
        config_builder=builder,
        factory=factory,
        run_preparer=prepare_custom_run,
        task_planner=plan_custom_tasks,
        domain_validator=lambda schema: [ConfigIssue(("factor",), "custom_rule", "Factor must be even")],
    )
    with pytest.raises(ConfigValidationError, match="factor: Factor must be even"):
        build_experiment_from_json(custom_json, registry=registry)
    builder.assert_not_called()
    factory.assert_not_called()


def test_custom_dependency_failure_stops_factory(custom_json):
    dependencies = Mock(side_effect=ExperimentDependencyError("custom prerequisite missing"))
    factory = Mock()
    registry = ExperimentConfigRegistry()
    registry.register(
        "custom",
        schema=CustomSchema,
        config_builder=build_custom_config,
        factory=factory,
        run_preparer=prepare_custom_run,
        task_planner=plan_custom_tasks,
        dependency_checker=dependencies,
    )
    with pytest.raises(ExperimentDependencyError, match="custom prerequisite missing"):
        build_experiment_from_json(custom_json, registry=registry)
    assert isinstance(dependencies.call_args.args[0], CustomConfig)
    factory.assert_not_called()


def test_custom_schema_errors_keep_original_paths():
    registry = ExperimentConfigRegistry()
    register_test_plugin(registry)
    with pytest.raises(ConfigValidationError) as error:
        validate_experiment_config(RawExperimentConfig(experiment_type="custom", factor=None), registry=registry)
    assert error.value.issues[0].path == ("factor",)


def test_builder_cannot_return_another_experiment_kind(custom_json):
    registry = ExperimentConfigRegistry()
    registry.register(
        "custom",
        schema=CustomSchema,
        config_builder=lambda schema: None,
        factory=CustomFactory,
        run_preparer=prepare_custom_run,
        task_planner=plan_custom_tasks,
    )
    with pytest.raises(ValueError, match="Config builder for 'custom'"):
        build_experiment_from_json(custom_json, registry=registry)


def test_installed_plugin_is_discovered_by_default(installed_plugin, custom_json):
    assert build_experiment_from_json(custom_json).experiment_name == "custom_factor_7"


def test_plugin_loading_can_be_disabled(installed_plugin):
    registry = create_default_experiment_registry(load_plugins=False)
    with pytest.raises(ExperimentRegistryError):
        registry.get("custom")


def test_plugin_load_is_idempotent_per_registry(installed_plugin):
    registry = create_default_experiment_registry()
    definition = registry.get("custom")
    registry.load_plugins()
    assert registry.get("custom") is definition


def test_cli_uses_installed_plugin(installed_plugin, custom_json, tmp_path, monkeypatch):
    import importlib

    from pysatl_experiment.utils import files_utils

    module = importlib.import_module("pysatl_experiment.cli.commands.build_and_run")
    monkeypatch.setattr(files_utils, "USER_DATA_DIR", str(tmp_path / "data"))
    files_utils.ensure_experiment_conf("external").write_text(custom_json.read_text())
    experiment = Mock()
    monkeypatch.setattr(module, "Experiment", experiment)
    result = CliRunner().invoke(module.build_and_run, ["external"])
    assert result.exit_code == 0, result.output
    assert experiment.call_args.args[0].experiment_name == "custom_factor_7"
    experiment.return_value.run_experiment.assert_called_once()


def test_plugin_failure_rolls_back_all_new_registrations(monkeypatch):
    from pysatl_experiment.experiment_execution import registry as module

    def broken_plugin(registry):
        register_test_plugin(registry)
        raise RuntimeError("incomplete installation")

    entry = Mock(name="entry", value="broken:register", dist=None)
    entry.name = "broken"
    entry.load.return_value = broken_plugin
    monkeypatch.setattr(module.metadata, "entry_points", lambda **kwargs: [entry])
    registry = create_default_experiment_registry(load_plugins=False)
    original = registry.validation_specs()
    with pytest.raises(ExperimentPluginError, match="broken.*incomplete installation"):
        registry.load_plugins()
    assert registry.validation_specs() == original


def test_entry_point_cannot_override_builtin(monkeypatch):
    from pysatl_experiment.experiment_execution import registry as module

    def duplicate(registry):
        registry.register(
            "power",
            schema=CustomSchema,
            config_builder=build_custom_config,
            factory=CustomFactory,
            run_preparer=prepare_custom_run,
            task_planner=plan_custom_tasks,
        )

    entry = Mock(value="duplicate:register", dist=None)
    entry.name = "duplicate"
    entry.load.return_value = duplicate
    monkeypatch.setattr(module.metadata, "entry_points", lambda **kwargs: [entry])
    with pytest.raises(ExperimentPluginError, match="duplicate.*already registered: power"):
        create_default_experiment_registry()


def test_missing_plugin_import_has_named_error(monkeypatch):
    from pysatl_experiment.experiment_execution import registry as module

    entry = metadata.EntryPoint(
        name="missing", value="nonexistent_pysatl_plugin:register", group=EXPERIMENT_ENTRY_POINT_GROUP
    )
    monkeypatch.setattr(module.metadata, "entry_points", lambda **kwargs: [entry])
    with pytest.raises(ExperimentPluginError, match="missing.*nonexistent_pysatl_plugin"):
        create_default_experiment_registry()


@pytest.mark.parametrize("handler", ["run_preparer", "task_planner"])
def test_registry_rejects_noncallable_run_handlers(handler):
    registry = ExperimentConfigRegistry()
    handlers = {"run_preparer": prepare_custom_run, "task_planner": plan_custom_tasks}
    handlers[handler] = None
    with pytest.raises(ExperimentRegistryError, match=f"{handler} must be callable"):
        registry.register(
            "custom",
            schema=CustomSchema,
            config_builder=build_custom_config,
            factory=CustomFactory,
            **handlers,
        )
    assert registry.validation_specs() == {}
