from abc import ABC, abstractmethod
from dataclasses import dataclass

from pysatl_criterion.persistence.model.common.data_storage.data_storage import DataModel, DataQuery, IDataStorage


@dataclass
class RandomValuesModel(DataModel):
    generator_name: str
    generator_parameters: list[float]
    sample_size: int
    sample_num: int
    data: list[float]


@dataclass
class RandomValuesQuery(DataQuery):
    generator_name: str
    generator_parameters: list[float]
    sample_size: int
    sample_num: int


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


class IRandomValuesStorage(IDataStorage[RandomValuesModel, RandomValuesQuery], ABC):
    """
    Random values storage interface.
    """

    @abstractmethod
    def get_rvs_count(self, query: RandomValuesAllQuery) -> int:
        """
        Get count of samples.
        """
        pass

    @abstractmethod
    def insert_all_data(self, query: RandomValuesAllModel) -> None:
        """
        Insert all data based on hypothesis and sample size.
        """
        pass

    @abstractmethod
    def get_all_data(self, query: RandomValuesAllQuery) -> list[RandomValuesModel] | None:
        """
        Get all data based on hypothesis and sample size.
        """
        pass

    @abstractmethod
    def delete_all_data(self, query: RandomValuesAllQuery) -> None:
        """
        Delete all data based on hypothesis and sample size.
        """
        pass

    @abstractmethod
    def get_count_data(self, query: RandomValuesCountQuery) -> list[RandomValuesModel] | None:
        """
        Get count data based on hypothesis and sample size.
        """
        pass
