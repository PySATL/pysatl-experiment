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
    data_generator_type: str
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
    data_generator_type: str
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

    pass
