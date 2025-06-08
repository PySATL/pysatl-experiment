from dataclasses import dataclass
from typing import Protocol

from pysatl_criterion.persistence.model.common.data_storage.data_storage import (
    DataModel,
    DataQuery,
    IDataStorage,
)


@dataclass
class RandomValuesModel(DataModel):
    generator_name: str
    generator_parameters: list[float]
    sample_size: int
    data: list[float]


@dataclass
class RandomValuesQuery(DataQuery):
    generator_name: str
    generator_parameters: list[float]
    sample_size: int


@dataclass
class RandomValuesAllQuery(DataQuery):
    generator_name: str
    generator_parameters: list[float]
    sample_size: int


@dataclass
class RandomValuesCountQuery(DataQuery):
    generator_name: str
    generator_parameters: list[float]
    sample_size: int
    count: int


@dataclass
class RandomValuesAllModel(DataModel):
    generator_name: str
    generator_parameters: list[float]
    sample_size: int
    data: list[list[float]]


class IRandomValuesStorage(IDataStorage[RandomValuesModel, RandomValuesQuery], Protocol):
    """
    Random values storage interface.
    """

    def get_rvs_count(self, query: RandomValuesAllQuery) -> int:
        """
        Get count of samples.
        """
        pass

    def insert_all_data(self, query: RandomValuesAllModel) -> None:
        """
        Insert all data based on hypothesis and sample size.
        """
        pass

    def get_all_data(self, query: RandomValuesAllQuery) -> list[RandomValuesModel]:
        """
        Get all data based on hypothesis and sample size.
        """
        pass

    def delete_all_data(self, query: RandomValuesAllQuery) -> None:
        """
        Delete all data based on hypothesis and sample size.
        """
        pass

    def get_count_data(self, query: RandomValuesCountQuery) -> list[RandomValuesModel]:
        """
        Get count data based on hypothesis and sample size.
        """
        pass
