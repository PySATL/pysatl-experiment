"""
Experiment storage models and interface.

Defines experiment configuration structures and storage contract.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol

from pysatl_criterion.persistence.models.base import DataModel, DataQuery, IDataStorage

from pysatl_experiment.configuration.models.step_status import ExperimentStep, StepStatus


@dataclass
class ExperimentModel(DataModel):
    """
    Experiment configuration and execution state.

    Parameters
    ----------
    experiment_type : str
        Type of experiment.
    storage_connection : str
        Storage backend connection string.
    run_mode : str
        Execution mode of experiment.
    report_mode : str
        Report generation mode.
    hypothesis : str
        Hypothesis identifier.
    generator_type : str
        Random generator type.
    executor_type : str
        Execution engine type.
    report_builder_type : str
        Report builder type.
    sample_sizes : list[int]
        List of sample sizes used in experiment.
    monte_carlo_count : int
        Number of Monte-Carlo simulations.
    criteria : dict[str, list[float]]
        Statistical criteria parameters.
    alternatives : dict[str, list[float]]
        Alternative hypothesis parameters.
    significance_levels : list[float]
        Significance levels (alpha values).
    parallel_workers : int
        Number of parallel workers.
    generation_status : StepStatus
        Lifecycle status of the generation step.
    execution_status : StepStatus
        Lifecycle status of the execution step.
    report_building_status : StepStatus
        Lifecycle status of the report building step.
    """

    experiment_type: str
    storage_connection: str
    run_mode: str
    report_mode: str
    hypothesis: str
    generator_type: str
    executor_type: str
    report_builder_type: str
    sample_sizes: list[int]
    monte_carlo_count: int
    criteria: dict[str, list[float]]
    alternatives: dict[str, list[float]]
    significance_levels: list[float]
    parallel_workers: int
    generation_status: StepStatus = field(default=StepStatus.PENDING)
    execution_status: StepStatus = field(default=StepStatus.PENDING)
    report_building_status: StepStatus = field(default=StepStatus.PENDING)


@dataclass
class ExperimentQuery(DataQuery):
    """
    Query for retrieving experiment configuration.

    Parameters
    ----------
    experiment_type : str
        Type of experiment.
    storage_connection : str
        Storage backend connection string.
    run_mode : str
        Execution mode.
    hypothesis : str
        Hypothesis identifier.
    generator_type : str
        Generator type.
    executor_type : str
        Executor type.
    report_builder_type : str
        Report builder type.
    sample_sizes : list[int]
        Sample sizes.
    monte_carlo_count : int
        Monte-Carlo iteration count.
    criteria : dict[str, list[float]]
        Criteria parameters.
    alternatives : dict[str, list[float]]
        Alternative parameters.
    significance_levels : list[float]
        Significance levels.
    report_mode : str
        Report mode.
    parallel_workers : int
        Number of workers.
    """

    experiment_type: str
    storage_connection: str
    run_mode: str
    hypothesis: str
    generator_type: str
    executor_type: str
    report_builder_type: str
    sample_sizes: list[int]
    monte_carlo_count: int
    criteria: dict[str, list[float]]
    alternatives: dict[str, list[float]]
    significance_levels: list[float]
    report_mode: str
    parallel_workers: int


class IExperimentStatusStorage(Protocol):
    """Persist lifecycle statuses for steps run by ``Experiment``."""

    def set_step_status(self, experiment_id: int, step: ExperimentStep, status: StepStatus) -> None:
        """
        Set the lifecycle status of an experiment step.

        Parameters
        ----------
        experiment_id : int
            Experiment identifier.
        step : ExperimentStep
            Pipeline step to update.
        status : StepStatus
            New lifecycle status.
        """


class IExperimentStorage(IDataStorage[ExperimentModel, ExperimentQuery], ABC):
    """Experiment configuration storage interface."""

    @abstractmethod
    def get_experiment_id(self, query: ExperimentQuery) -> int | None:
        """
        Get experiment ID for a given query.

        Parameters
        ----------
        query : ExperimentQuery

        Returns
        -------
        int | None
        """
        pass

    @abstractmethod
    def set_step_status(self, experiment_id: int, step: ExperimentStep, status: StepStatus) -> None:
        """
        Set the lifecycle status of an experiment step.

        Parameters
        ----------
        experiment_id : int
            Experiment identifier.
        step : ExperimentStep
            Pipeline step to update.
        status : StepStatus
            New lifecycle status.
        """
        pass
