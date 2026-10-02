"""Storage contract for time complexity."""

from abc import ABC

from pysatl_criterion.persistence.models.base import IDataStorage

from pysatl_experiment.persistence.contracts.bulk import IBulkDataStorage
from pysatl_experiment.persistence.models.time_complexity import (
    TimeComplexityFilter,
    TimeComplexityModel,
    TimeComplexityQuery,
)


class ITimeComplexityStorage(
    IDataStorage[TimeComplexityModel, TimeComplexityQuery],
    IBulkDataStorage[TimeComplexityModel, TimeComplexityFilter],
    ABC,
):
    """Read timing results in pages and upsert them in atomic batches."""
