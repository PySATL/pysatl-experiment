from dataclasses import dataclass
from typing import Protocol

from pysatl_criterion.persistence.model.common.data_storage.data_storage import DataModel, DataQuery, IDataStorage


@dataclass
class TimeComplexityModel(DataModel):
    experiment_id: int
    criterion_code: str
    criterion_parameters: list[float]
    sample_size: int
    monte_carlo_count: int
    results_times: list[float]


@dataclass
class TimeComplexityQuery(DataQuery):
    criterion_code: str
    criterion_parameters: list[float]
    sample_size: int
    monte_carlo_count: int


class ITimeComplexityStorage(IDataStorage[TimeComplexityModel, TimeComplexityQuery], Protocol):
    """
    Time complexity storage interface.
    """

    def init(self) -> None:
        """
        Initialize SQLite time complexity storage and create tables.
        """

    def insert_data(self, data: TimeComplexityModel) -> None:
        """
        Insert or replace time complexity data.
        """

    def get_data(self, query: TimeComplexityQuery) -> TimeComplexityModel | None:
        """
        Get time complexity data matching the query.
        """

    def delete_data(self, query: TimeComplexityQuery) -> None:
        """
        Delete time complexity data matching the query.
        """
