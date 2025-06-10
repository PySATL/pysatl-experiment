from dataclasses import dataclass
from typing import Protocol

from pysatl_criterion.persistence.model.common.data_storage.data_storage import (
    DataModel,
    DataQuery,
    IDataStorage,
)


@dataclass
class ExperimentModel(DataModel):
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
    is_generation_done: bool
    is_execution_done: bool
    is_report_building_done: bool


@dataclass
class ExperimentQuery(DataQuery):
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


class IExperimentStorage(IDataStorage[ExperimentModel, ExperimentQuery], Protocol):
    """
    Experiment configuration storage interface.
    """

    def get_experiment_id(self, query: ExperimentQuery) -> int:
        """
        Get experiment id.

        :return: experiment id
        """
        pass

    def set_generation_done(self, experiment_id: int) -> None:
        """
        Set generation step as done.

        :param experiment_id: experiment id.
        """
        pass

    def set_execution_done(self, experiment_id: int) -> None:
        """
        Set execution step as done.

        :param experiment_id: experiment id.
        """
        pass

    def set_report_building_done(self, experiment_id: int) -> None:
        """
        Set report building step as done.

        :param experiment_id: experiment id.
        """
        pass
