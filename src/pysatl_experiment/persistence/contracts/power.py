"""Storage contract for power."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from pysatl_criterion.persistence.models.base import IDataStorage

from pysatl_experiment.persistence.models.power import PowerModel, PowerQuery


class IPowerStorage(IDataStorage[PowerModel, PowerQuery], ABC):
    """Power storage interface."""

    @abstractmethod
    def bulk_insert_data(self, data_list: Iterable[PowerModel]) -> None:
        """
        Insert or update multiple power records.

        Parameters
        ----------
        data_list : Iterable[PowerModel]
            Power results to store.
        """
        pass
