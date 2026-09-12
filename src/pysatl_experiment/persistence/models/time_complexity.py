"""Time complexity storage models and interface."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeAlias

from pysatl_criterion.persistence.models.base import DataModel, DataQuery, IDataStorage


@dataclass
class TimeComplexityModel(DataModel):
    """
    Time complexity measurement model.

    Parameters
    ----------
    experiment_name : str
        Experiment name.
    criterion_code : str
        Criterion identifier.
    criterion_parameters : dict[str, float]
        Criterion parameters.
    sample_size : int
        Sample size.
    samples_count : int
        Number of simulations.
    results_times : list[float]
        Execution time measurements.
    """

    experiment_name: str
    criterion_code: str
    criterion_parameters: dict[str, float]
    sample_size: int
    samples_count: int
    results_times: list[float]


@dataclass
class TimeComplexityQuery(DataQuery):
    """
    Query for time complexity data.

    Parameters
    ----------
    experiment_name : str
        Experiment name.
    criterion_code : str
    criterion_parameters : CriterionParameters
    sample_size : int
    samples_count : int
    """

    experiment_name: str
    criterion_code: str
    criterion_parameters: dict[str, float]
    sample_size: int
    samples_count: int


class ITimeComplexityStorage(IDataStorage[TimeComplexityModel, TimeComplexityQuery], ABC):
    """Time complexity storage interface."""

    @abstractmethod
    def bulk_insert_data(self, data_list: Iterable[TimeComplexityModel]) -> None:
        """
        Insert or update multiple time complexity records.

        Parameters
        ----------
        data_list : Iterable[TimeComplexityModel]
            Time complexity measurements to store.
        """
        pass
