"""Experiment-owned empirical limit distributions."""

from dataclasses import dataclass

from pysatl_criterion.persistence.models.base import DataModel, DataQuery


@dataclass
class LimitDistributionQuery(DataQuery):
    """Identify a result within one named experiment."""

    experiment_name: str
    criterion_code: str
    criterion_parameters: dict[str, float] | list[float]
    sample_size: int
    monte_carlo_count: int


@dataclass
class LimitDistributionModel(DataModel):
    """Computed statistic values belonging to a named experiment."""

    experiment_name: str
    criterion_code: str
    criterion_parameters: dict[str, float] | list[float]
    sample_size: int
    monte_carlo_count: int
    results_statistics: list[float]
