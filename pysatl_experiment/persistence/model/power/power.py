"""Power storage models and interface."""

from abc import ABC
from dataclasses import dataclass

from pysatl_criterion.persistence.model.common.data_storage.data_storage import DataModel, DataQuery, IDataStorage


@dataclass
class PowerModel(DataModel):
    """
    Power analysis result model.

    Parameters
    ----------
    experiment_id : int
        Experiment identifier.
    criterion_code : str
        Statistical criterion code.
    criterion_parameters : list[float]
        Parameters of criterion.
    sample_size : int
        Sample size.
    alternative_code : str
        Alternative hypothesis code.
    alternative_parameters : list[float]
        Parameters of alternative hypothesis.
    monte_carlo_count : int
        Number of simulations.
    significance_level : float
        Significance level alpha.
    results_criteria : list[bool]
        Simulation results (rejections / non-rejections).
    """

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
    """
    Query for retrieving power results.

    Parameters
    ----------
    criterion_code : str
    criterion_parameters : list[float]
    sample_size : int
    alternative_code : str
    alternative_parameters : list[float]
    monte_carlo_count : int
    significance_level : float
    """

    criterion_code: str
    criterion_parameters: list[float]
    sample_size: int
    alternative_code: str
    alternative_parameters: list[float]
    monte_carlo_count: int
    significance_level: float


class IPowerStorage(IDataStorage[PowerModel, PowerQuery], ABC):
    """Power storage interface."""

    pass
