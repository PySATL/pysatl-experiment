from dataclasses import dataclass
from typing import Protocol

from pysatl_criterion.persistence.model.common.data_storage.data_storage import DataModel, DataQuery, IDataStorage


@dataclass
class PowerModel(DataModel):
    experiment_id: int
    criterion_code: str
    criterion_parameters: list[float]
    sample_size: int
    alternative_code: str
    alternative_parameters: list[float]
    monte_carlo_count: int
    significance_level: float
    results_criteria: list[bool]


@dataclass
class PowerQuery(DataQuery):
    criterion_code: str
    criterion_parameters: list[float]
    sample_size: int
    alternative_code: str
    alternative_parameters: list[float]
    monte_carlo_count: int
    significance_level: float


class IPowerStorage(IDataStorage[PowerModel, PowerQuery], Protocol):
    """
    Power storage interface.
    """

    def init(self) -> None:
        """
        Initialize SQLite power storage and create tables.
        """

    def insert_data(self, data: PowerModel) -> None:
        """
        Insert or replace a power entry.
        """

    def get_data(self, query: PowerQuery) -> PowerModel | None:
        """
        Retrieve power data matching the query.
        """

    def delete_data(self, query: PowerQuery) -> None:
        """
        Delete power data matching the query.
        """
