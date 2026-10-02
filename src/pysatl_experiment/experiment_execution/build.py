"""Public boundary from JSON input to registered experiment factories."""

from pathlib import Path
from typing import Any

from pysatl_experiment.configuration.config_loader import read_raw_experiment_config
from pysatl_experiment.configuration import ExperimentConfig
from pysatl_experiment.configuration.validation import validate_experiment_config
from pysatl_experiment.experiment_execution.experiment_steps import ExperimentSteps
from pysatl_experiment.experiment_execution.registry import (
    ExperimentConfigRegistry,
    ExperimentFactory,
    create_default_experiment_registry,
)


def get_experiment_factory(
    experiment_type: str, *, registry: ExperimentConfigRegistry | None = None
) -> ExperimentFactory[Any, Any, Any, Any]:
    """Create the factory supplied by an experiment's registration."""
    if registry is None:
        registry = create_default_experiment_registry()
    return registry.get(experiment_type).factory()


def build_experiment(config: ExperimentConfig, *, registry: ExperimentConfigRegistry | None = None) -> ExperimentSteps:
    """Check dependencies, initialize stores, prepare the run, plan and assemble steps."""
    if registry is None:
        registry = create_default_experiment_registry()
    definition = registry.get(config.experiment_type)
    if definition.dependency_checker is not None:
        definition.dependency_checker(config)
    factory = get_experiment_factory(config.experiment_type, registry=registry)
    storages = factory.create_storages(config)
    state = definition.run_preparer(config, storages)
    plan = definition.task_planner(config, storages, state)
    return factory.create_experiment_steps(config, storages, state, plan)


def build_experiment_from_json(
    path: str | Path, *, registry: ExperimentConfigRegistry | None = None
) -> ExperimentSteps:
    """Use one registry for the entire load, validation and assembly pipeline."""
    raw = read_raw_experiment_config(path)
    if registry is None:
        registry = create_default_experiment_registry()
    config = validate_experiment_config(raw, registry=registry)
    return build_experiment(config, registry=registry)
