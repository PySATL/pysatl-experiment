from dataclasses import dataclass
from typing import Protocol

from pysatl_criterion.persistence.model.common.data_storage.data_storage import (
    DataModel,
    DataQuery,
    IDataStorage,
)


@dataclass
class RandomValuesModel(DataModel):
    experiment_id: int
    generator_code: str
    generator_parameters: list[float]
    sample_size: int
    sample_num: int
    data: list[float]


@dataclass
class RandomValuesQuery(DataQuery):
    generator_code: str
    generator_parameters: list[float]
    sample_size: int


class IRandomValuesStorage(IDataStorage[RandomValuesModel, RandomValuesQuery], Protocol):
    """
    Random values storage interface.
    """

    def get_rvs_count(self, query: RandomValuesQuery) -> int:
        """
        Get count of samples.
        """
        pass
