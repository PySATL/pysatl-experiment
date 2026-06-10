"""Time complexity storage models and interface."""

from abc import ABC
from dataclasses import dataclass

from pysatl_criterion.persistence.models.base import DataModel, DataQuery, IDataStorage


@dataclass
class TimeComplexityModel(DataModel):
    """
    Time complexity measurement model.

    Parameters
    ----------
    experiment_id : int
        Experiment identifier.
    criterion_code : str
        Criterion identifier.
    criterion_parameters : list[float]
        Criterion parameters.
    sample_size : int
        Sample size.
    monte_carlo_count : int
        Number of simulations.
    results_times : list[float]
        Execution time measurements.
    """

    experiment_id: int
    criterion_code: str
    criterion_parameters: list[float]
    sample_size: int
    monte_carlo_count: int
    results_times: list[float]


@dataclass
class TimeComplexityQuery(DataQuery):
    """
    Query for time complexity data.

    Parameters
    ----------
    criterion_code : str
    criterion_parameters : list[float]
    sample_size : int
    monte_carlo_count : int
    """

    criterion_code: str
    criterion_parameters: list[float]
    sample_size: int
    monte_carlo_count: int


class ITimeComplexityStorage(IDataStorage[TimeComplexityModel, TimeComplexityQuery], ABC):
    """Time complexity storage interface."""

    pass
