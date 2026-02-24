from abc import ABC
from dataclasses import dataclass

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


class IPowerStorage(IDataStorage[PowerModel, PowerQuery], ABC):
    """
    Power storage interface.
    """

    pass
