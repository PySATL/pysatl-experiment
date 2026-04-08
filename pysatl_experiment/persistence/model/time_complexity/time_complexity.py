from abc import ABC
from dataclasses import dataclass

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


class ITimeComplexityStorage(IDataStorage[TimeComplexityModel, TimeComplexityQuery], ABC):
    """
    Time complexity storage interface.
    """

    pass
