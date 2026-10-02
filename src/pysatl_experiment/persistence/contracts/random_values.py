"""Storage contract for random values."""

from abc import ABC, abstractmethod

from pysatl_experiment.persistence.contracts.bulk import IBulkDataStorage
from pysatl_experiment.persistence.models.random_values import RandomValuesFilter, RandomValuesModel


class IRandomValuesStorage(IBulkDataStorage[RandomValuesModel, RandomValuesFilter], ABC):
    """Store samples in batches, always scoped to an explicitly named experiment."""

    @abstractmethod
    def count(self, query: RandomValuesFilter) -> int:
        """Count matching samples, not the individual numbers inside them."""

    @abstractmethod
    def delete(self, query: RandomValuesFilter) -> int:
        """Delete matching samples and return the number of deleted records."""
