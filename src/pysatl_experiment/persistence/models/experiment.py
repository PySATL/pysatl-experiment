"""
Experiment storage models and interface.

Defines experiment configuration structures and storage contract.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pysatl_criterion.persistence.models.base import DataModel, DataQuery, IDataStorage


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
    is_generation_done : bool
        Whether generation step is completed.
    is_execution_done : bool
        Whether execution step is completed.
    is_report_building_done : bool
        Whether report building step is completed.
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
    is_generation_done: bool
    is_execution_done: bool
    is_report_building_done: bool


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
    def set_generation_done(self, experiment_id: int) -> None:
        """
        Mark generation step as completed.

        Parameters
        ----------
        experiment_id : int
        """
        pass

    @abstractmethod
    def set_execution_done(self, experiment_id: int) -> None:
        """
        Mark execution step as completed.

        Parameters
        ----------
        experiment_id : int
        """
        pass

    @abstractmethod
    def set_report_building_done(self, experiment_id: int) -> None:
        """
        Mark report building step as completed.

        Parameters
        ----------
        experiment_id : int
        """
        pass
