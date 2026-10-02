"""Data models and queries for power."""

from dataclasses import dataclass

from pysatl_criterion.persistence.models.base import DataModel, DataQuery


@dataclass
class PowerModel(DataModel):
    """
    Power analysis result model.

    Parameters
    ----------
    experiment_name : str
        Experiment identifier.
    criterion_code : str
        Statistical criterion code.
    criterion_parameters : list[float]
        Parameters of criterion.
    sample_size : int
        Sample size.
    alternative_code : str
        Alternative hypothesis code.
    alternative_parameters : dict[str, float | list[float]] | list[float]
        Parameters of alternative hypothesis.
    monte_carlo_count : int
        Number of simulations.
    significance_level : float
        Significance level alpha.
    results_criteria : list[bool]
        Simulation results (rejections / non-rejections).
    """

    experiment_name: str
    criterion_code: str
    criterion_parameters: dict[str, float] | list[float]
    sample_size: int
    alternative_code: str
    alternative_parameters: dict[str, float | list[float]] | list[float]
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
    alternative_parameters : dict[str, float | list[float]] | list[float]
    monte_carlo_count : int
    significance_level : float
    """

    experiment_name: str
    criterion_code: str
    criterion_parameters: dict[str, float] | list[float]
    sample_size: int
    alternative_code: str
    alternative_parameters: dict[str, float | list[float]] | list[float]
    monte_carlo_count: int
    significance_level: float
