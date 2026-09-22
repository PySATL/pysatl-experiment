"""Random values storage models and interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from pysatl_criterion.persistence.models.base import DataModel, DataQuery, IDataStorage

from pysatl_experiment.configuration.models.parameters import NumericParameters


@dataclass
class RandomValuesModel(DataModel):
    """
    Random values sample model.

    Parameters
    ----------
    generator_code : str
        Name of generator.
    generator_parameters : NumericParameters
        Generator parameters.
    sample_size : int
        Size of each sample.
    experiment_name : str
        Sample index.
    data : list[float]
        Generated random values.
    """

    generator_code: str
    generator_parameters: NumericParameters
    sample_size: int
    experiment_name: str
    data: list[float]

    # TODO: check for actual usage
    # @staticmethod
    # def from_row(query: RandomValuesAllQuery) -> RandomValuesModel:
    #     return RandomValuesModel()


@dataclass
class RandomValuesQuery(DataQuery):
    """
    Query for single random sample.

    Parameters
    ----------
    generator_code : str
    sample_size : int
    experiment_name : str
    """

    generator_code: str
    sample_size: int
    experiment_name: str
    generator_parameters: dict[str, Any] | list[float] | None = None


@dataclass
class RandomValuesAllQuery(DataQuery):
    """
    Query for all samples of generator.

    Parameters
    ----------
    generator_code : str
    sample_size : int
    """

    generator_code: str
    sample_size: int
    experiment_name: str = ""
    generator_parameters: dict[str, Any] | list[float] | None = None


@dataclass
class RandomValuesCountQuery(DataQuery):
    """
    Query for limited number of samples.

    Parameters
    ----------
    generator_code : str
    sample_size : int
    count : int
    """

    generator_code: str
    sample_size: int
    count: int
    experiment_name: str = ""
    generator_parameters: dict[str, Any] | list[float] | None = None


@dataclass(init=False)
class RandomValuesAllModel(DataModel):
    """
    Bulk random values container.

    Parameters
    ----------
    generator_code : str
    experiment_name : str
    generator_parameters : dict[str, float]
    sample_size : int
    data : list[list[float]]
    """

    generator_code: str
    experiment_name: str
    sample_size: int
    generator_parameters: dict[str, float] | list[float]
    data: list[list[float]]

    def __init__(
        self,
        sample_size: int,
        generator_parameters: dict[str, float] | list[float],
        data: list[list[float]],
        generator_code: str | None = None,
        generator_name: str | None = None,
        experiment_name: str = "",
    ) -> None:
        self.generator_code = generator_code if generator_code is not None else str(generator_name)
        self.experiment_name = experiment_name
        self.sample_size = sample_size
        self.generator_parameters = generator_parameters
        self.data = data


class IRandomValuesStorage(IDataStorage[RandomValuesModel, RandomValuesQuery], ABC):
    """Random values storage interface."""

    @abstractmethod
    def get_rvs_count(self, query: RandomValuesAllQuery) -> int:
        """
        Get count of samples.

        Parameters
        ----------
        query : RandomValuesAllModel
        """
        pass

    @abstractmethod
    def bulk_insert_data(self, data_list: Iterable[RandomValuesModel]) -> None:
        """
        Insert all data based on hypothesis and sample size.

        Parameters
        ----------
        data_list : list[RandomValuesModel]
        """
        pass

    @abstractmethod
    def get_all_data(self, query: RandomValuesAllQuery) -> list[RandomValuesModel] | None:
        """
        Get all data based on hypothesis and sample size.

        Parameters
        ----------
        query : RandomValuesAllQuery

        Returns
        -------
        list[RandomValuesModel] | None
        """
        pass

    @abstractmethod
    def delete_all_data(self, query: RandomValuesAllQuery) -> None:
        """
        Delete all data based on hypothesis and sample size.

        Parameters
        ----------
        query : RandomValuesAllQuery
        """
        pass

    @abstractmethod
    def get_count_data(self, query: RandomValuesCountQuery) -> list[RandomValuesModel] | None:
        """
        Get count data based on hypothesis and sample size.

        Parameters
        ----------
        query : RandomValuesCountQuery

        Returns
        -------
        list[RandomValuesModel] | None
        """
        pass
