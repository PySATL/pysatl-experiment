"""Public registration of experiment validation, construction and dependencies."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel

from pysatl_experiment.configuration import ExperimentConfig
from pysatl_experiment.configuration.validation import ConfigIssue, ExperimentValidationSpec, create_config_validator
from pysatl_experiment.experiment_execution.dependencies import check_experiment_dependencies
from pysatl_experiment.experiment_execution.experiment_steps import ExperimentSteps


EXPERIMENT_ENTRY_POINT_GROUP = "pysatl_experiment.experiments"
SchemaT = TypeVar("SchemaT", bound=BaseModel)
ConfigT = TypeVar("ConfigT", bound=ExperimentConfig)
StoragesT = TypeVar("StoragesT")
StateT = TypeVar("StateT")
PlanT = TypeVar("PlanT")
FactoryStateT = TypeVar("FactoryStateT", contravariant=True)
FactoryPlanT = TypeVar("FactoryPlanT", contravariant=True)
FactoryConfigT = TypeVar("FactoryConfigT", bound=ExperimentConfig, contravariant=True)


class ExperimentFactory(Protocol[FactoryConfigT, StoragesT, FactoryStateT, FactoryPlanT]):
    """Minimal factory contract for built-in and external experiment kinds."""

    def create_storages(self, experiment_config: FactoryConfigT, /) -> StoragesT:
        """Create and initialize the dependencies used by this experiment kind."""
        ...

    def create_experiment_steps(
        self, experiment_config: FactoryConfigT, storages: StoragesT, state: FactoryStateT, plan: FactoryPlanT, /
    ) -> ExperimentSteps:
        """Build the steps belonging to a prepared experiment configuration."""
        ...


class ExperimentRegistryError(ValueError):
    """Report duplicate, invalid or missing experiment registrations."""


class ExperimentPluginError(RuntimeError):
    """Identify an installed plugin that failed to load or register."""


@dataclass(frozen=True)
class ExperimentDefinition(Generic[ConfigT, StoragesT, StateT, PlanT]):
    """One registration connecting the types produced and consumed by its handlers."""

    validation: ExperimentValidationSpec
    factory: Callable[[], ExperimentFactory[ConfigT, StoragesT, StateT, PlanT]]
    run_preparer: Callable[[ConfigT, StoragesT], StateT]
    task_planner: Callable[[ConfigT, StoragesT, StateT], PlanT]
    dependency_checker: Callable[[ConfigT], None] | None


class ExperimentConfigRegistry:
    """An isolated set of complete experiment registrations."""

    def __init__(self) -> None:
        # Only heterogeneous storage erases types; register() checks each handler chain.
        self._definitions: dict[str, ExperimentDefinition[Any, Any, Any, Any]] = {}
        self._loaded_plugins: set[tuple[str, str, str]] = set()

    def register(
        self,
        experiment_type: str,
        *,
        schema: type[SchemaT],
        config_builder: Callable[[SchemaT], ConfigT],
        factory: Callable[[], ExperimentFactory[ConfigT, StoragesT, StateT, PlanT]],
        run_preparer: Callable[[ConfigT, StoragesT], StateT],
        task_planner: Callable[[ConfigT, StoragesT, StateT], PlanT],
        dependency_checker: Callable[[ConfigT], None] | None = None,
        domain_validator: Callable[[SchemaT], list[ConfigIssue]] | None = None,
    ) -> None:
        """Register all handlers for a kind; existing names cannot be replaced."""
        if not isinstance(experiment_type, str) or not experiment_type.strip():
            raise ExperimentRegistryError("experiment_type must be a nonempty string")
        if experiment_type in self._definitions:
            raise ExperimentRegistryError(f"Experiment type already registered: {experiment_type}")
        if not isinstance(schema, type) or not issubclass(schema, BaseModel):
            raise ExperimentRegistryError("schema must be a Pydantic BaseModel class")
        for name, callback in (
            ("config_builder", config_builder),
            ("factory", factory),
            ("run_preparer", run_preparer),
            ("task_planner", task_planner),
        ):
            if not callable(callback):
                raise ExperimentRegistryError(f"{name} must be callable")
        for name, optional_callback in (
            ("dependency_checker", dependency_checker),
            ("domain_validator", domain_validator),
        ):
            if optional_callback is not None and not callable(optional_callback):
                raise ExperimentRegistryError(f"{name} must be callable or None")
        self._definitions[experiment_type] = ExperimentDefinition(
            validation=ExperimentValidationSpec(schema, config_builder, domain_validator),
            factory=factory,
            run_preparer=run_preparer,
            task_planner=task_planner,
            dependency_checker=dependency_checker,
        )

    def get(self, experiment_type: str) -> ExperimentDefinition[Any, Any, Any, Any]:
        """Look up the complete definition of a registered kind."""
        try:
            return self._definitions[experiment_type]
        except KeyError as error:
            raise ExperimentRegistryError(f"Unsupported experiment type: {experiment_type}") from error

    def validation_specs(self) -> Mapping[str, ExperimentValidationSpec]:
        """Expose only validation data to the configuration layer."""
        return {kind: definition.validation for kind, definition in self._definitions.items()}

    def load_plugins(self) -> None:
        """Load entry point registration functions atomically and once per registry."""
        staged = ExperimentConfigRegistry()
        staged._definitions = dict(self._definitions)
        staged._loaded_plugins = set(self._loaded_plugins)
        entries = sorted(
            metadata.entry_points(group=EXPERIMENT_ENTRY_POINT_GROUP), key=lambda entry: (entry.name, entry.value)
        )
        for entry in entries:
            distribution = entry.dist.name if entry.dist is not None else ""
            identity = (distribution, entry.name, entry.value)
            if identity in staged._loaded_plugins:
                continue
            try:
                register = entry.load()
                if not callable(register):
                    raise TypeError("Entry point must be a callable accepting an ExperimentConfigRegistry")
                register(staged)
            except Exception as error:
                raise ExperimentPluginError(
                    f"Cannot load experiment plugin '{entry.name}' ({entry.value}): {error}"
                ) from error
            staged._loaded_plugins.add(identity)
        self._definitions = staged._definitions
        self._loaded_plugins = staged._loaded_plugins


def create_default_experiment_registry(*, load_plugins: bool = True) -> ExperimentConfigRegistry:
    """Register built-ins and, by default, discover installed experiment plugins."""
    from pysatl_experiment.configuration.validation.config_schemas import (
        CriticalValueSchema,
        PowerSchema,
        TimeComplexitySchema,
    )
    from pysatl_experiment.configuration.validation.config_validator import (
        build_critical_value_config,
        build_power_config,
        build_time_complexity_config,
    )
    from pysatl_experiment.experiment_execution.experiment_factory import (
        CriticalValueExperimentFactory,
        PowerExperimentFactory,
        TimeComplexityExperimentFactory,
    )
    from pysatl_experiment.experiment_execution.planning.critical_value import plan_critical_value_tasks
    from pysatl_experiment.experiment_execution.planning.power import plan_power_tasks
    from pysatl_experiment.experiment_execution.planning.time_complexity import plan_time_complexity_tasks
    from pysatl_experiment.experiment_execution.run_preparation import prepare_experiment

    registry = ExperimentConfigRegistry()
    specs = create_config_validator().validation_specs()
    registry.register(
        "critical_value",
        schema=CriticalValueSchema,
        config_builder=build_critical_value_config,
        factory=CriticalValueExperimentFactory,
        run_preparer=prepare_experiment,
        task_planner=plan_critical_value_tasks,
        domain_validator=specs["critical_value"].domain_issues,
    )
    registry.register(
        "power",
        schema=PowerSchema,
        config_builder=build_power_config,
        factory=PowerExperimentFactory,
        run_preparer=prepare_experiment,
        task_planner=plan_power_tasks,
        domain_validator=specs["power"].domain_issues,
        dependency_checker=check_experiment_dependencies,
    )
    registry.register(
        "time_complexity",
        schema=TimeComplexitySchema,
        config_builder=build_time_complexity_config,
        factory=TimeComplexityExperimentFactory,
        run_preparer=prepare_experiment,
        task_planner=plan_time_complexity_tasks,
        domain_validator=specs["time_complexity"].domain_issues,
    )
    if load_plugins:
        registry.load_plugins()
    return registry
