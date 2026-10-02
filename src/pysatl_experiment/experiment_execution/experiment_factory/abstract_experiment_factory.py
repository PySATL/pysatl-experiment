"""Assemble initialized storages and steps from an explicitly prepared run."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pysatl_criterion.persistence.models.base import IDataStorage

from pysatl_experiment.configuration import ExperimentConfig
from pysatl_experiment.experiment_execution.experiment_config_adapter import ExperimentConfigAdapter
from pysatl_experiment.experiment_execution.experiment_steps import ExperimentSteps
from pysatl_experiment.experiment_execution.experiment_storages import ExperimentStorages
from pysatl_experiment.experiment_execution.planning.plan import ExperimentTaskPlan
from pysatl_experiment.experiment_execution.run_state import ExperimentRunState
from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.persistence.contracts.experiment import IExperimentStorage
from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.sqlalchemy.experiment import AlchemyExperimentStorage
from pysatl_experiment.persistence.sqlalchemy.random_values import AlchemyRandomValuesStorage


D = TypeVar("D", bound=ExperimentConfig)
G = TypeVar("G", bound=IExperimentStep)
E = TypeVar("E", bound=IExperimentStep)
R = TypeVar("R", bound=IExperimentStep)
GenerationTaskT = TypeVar("GenerationTaskT")
ExecutionTaskT = TypeVar("ExecutionTaskT")
RS = TypeVar("RS", bound=IDataStorage)


class AbstractExperimentFactory(Generic[D, G, E, R, RS, GenerationTaskT, ExecutionTaskT], ABC):
    """Create dependencies and assemble steps without managing run progress."""

    config: D

    @property
    def config_adapter(self) -> ExperimentConfigAdapter:
        """Adapt configuration to runtime objects without accessing storage."""
        return ExperimentConfigAdapter(self.config)

    def create_storages(self, experiment_config: D) -> ExperimentStorages[RS]:
        """Create and initialize tables without reading or changing run data."""
        self.config = experiment_config
        return ExperimentStorages(
            data=self._init_data_storage(),
            result=self._init_result_storage(),
            experiment=self._init_experiment_storage(),
        )

    def create_experiment_steps(
        self,
        experiment_config: D,
        storages: ExperimentStorages[RS],
        state: ExperimentRunState,
        plan: ExperimentTaskPlan[GenerationTaskT, ExecutionTaskT],
    ) -> ExperimentSteps:
        """Assemble exactly the steps requested by the prepared plan."""
        self.config = experiment_config
        return ExperimentSteps(
            experiment_name=self.config.experiment_name,
            experiment_storage=storages.experiment,
            generation_step=None
            if plan.generation is None
            else self._create_generation_step(storages.data, plan.generation),
            execution_step=None
            if plan.execution is None
            else self._create_execution_step(storages.data, storages.result, plan.execution),
            report_building_step=self._create_report_building_step(storages.result),
        )

    @abstractmethod
    def _create_generation_step(self, data_storage: IRandomValuesStorage, tasks: list[GenerationTaskT]) -> G:
        """Assemble the generation step from prepared tasks."""

    def _init_data_storage(self) -> IRandomValuesStorage:
        storage = AlchemyRandomValuesStorage(self.config.storage_connection)
        storage.init()
        return storage

    def _init_experiment_storage(self) -> IExperimentStorage:
        storage = AlchemyExperimentStorage(self.config.storage_connection)
        storage.init()
        return storage

    @abstractmethod
    def _init_result_storage(self) -> RS:
        """Initialize result storage for this experiment kind."""

    @abstractmethod
    def _create_execution_step(
        self,
        data_storage: IRandomValuesStorage,
        result_storage: RS,
        step_config: list[ExecutionTaskT],
    ) -> E:
        """Assemble the execution step from prepared tasks."""

    @abstractmethod
    def _create_report_building_step(self, result_storage: RS) -> R:
        """Create a report from report settings and execution metadata."""
