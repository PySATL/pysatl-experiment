"""Typed extension with custom stores, state and a nonstandard plan container."""

from dataclasses import dataclass

from pysatl_experiment.configuration import CriticalValueExperimentConfig
from pysatl_experiment.configuration.validation.config_schemas import CriticalValueSchema
from pysatl_experiment.configuration.validation.config_validator import build_critical_value_config
from pysatl_experiment.experiment_execution.experiment_steps import ExperimentSteps
from pysatl_experiment.experiment_execution.planning.plan import ExperimentTaskPlan
from pysatl_experiment.experiment_execution.registry import ExperimentConfigRegistry


@dataclass
class CustomStores:
    location: str


@dataclass
class CustomState:
    checkpoint: int


@dataclass
class CustomPlan:
    jobs: tuple[str, ...]


class CustomFactory:
    def create_storages(self, config: CriticalValueExperimentConfig) -> CustomStores:
        return CustomStores(config.storage_connection)

    def create_experiment_steps(
        self, config: CriticalValueExperimentConfig, stores: CustomStores, state: CustomState, plan: CustomPlan
    ) -> ExperimentSteps:
        raise NotImplementedError


def prepare(config: CriticalValueExperimentConfig, stores: CustomStores) -> CustomState:
    return CustomState(0)


def plan(config: CriticalValueExperimentConfig, stores: CustomStores, state: CustomState) -> CustomPlan:
    return CustomPlan(("custom job",))


def wrong_plan(config: CriticalValueExperimentConfig, stores: CustomStores, state: CustomState) -> str:
    return "incompatible plan"


# The shared container also accepts task types unknown to the library.
custom_tasks: ExperimentTaskPlan[str, int] = ExperimentTaskPlan(generation=["sample"], execution=[42])
registry = ExperimentConfigRegistry()
registry.register(
    "critical_value",
    schema=CriticalValueSchema,
    config_builder=build_critical_value_config,
    factory=CustomFactory,
    run_preparer=prepare,
    task_planner=plan,
)
