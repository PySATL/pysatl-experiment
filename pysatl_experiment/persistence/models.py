"""
Generic storage interfaces for experiment system.

This module defines abstract base classes for:
- random value storage (RVS)
- critical value storage
- result storage
"""

from abc import ABC, abstractmethod
from typing import Any


class IStore:
    """
    Base storage interface.

    Provides lifecycle hooks for all stores.
    """

    def migrate(self):
        """
        Run database migrations.

        Returns
        -------
        None
        """
        pass

    def init(self):
        """
        Initialize storage backend.

        Returns
        -------
        None
        """
        pass


class IRvsStore(IStore, ABC):
    """Random values storage interface."""

    def insert_all_rvs(self, generator_code: str, size: int, data: list[list[float]]):
        """
        Insert multiple RVS samples.

        Parameters
        ----------
        generator_code : str
            Generator identifier.
        size : int
            Sample size.
        data : list[list[float]]
            List of samples.

        Returns
        -------
        None
        """
        for d in data:
            self.insert_rvs(generator_code, size, d)

    @abstractmethod
    def insert_rvs(self, generator_code: str, size: int, data: list[float]):
        """
        Insert single RVS sample.

        Parameters
        ----------
        generator_code : str
            Generator identifier.
        size : int
            Sample size.
        data : list[float]
            Sample data.

        Returns
        -------
        None
        """
        pass

    def get_rvs_count(self, generator_code: str, size: int) -> int:
        """
        Count stored RVS samples.

        Parameters
        ----------
        generator_code : str
            Generator identifier.
        size : int
            Sample size.

        Returns
        -------
        int
            Number of stored samples.
        """
        return len(self.get_rvs(generator_code, size))

    @abstractmethod
    def get_rvs(self, generator_code: str, size: int) -> list[list[float]]:
        """
        Get all RVS samples.

        Parameters
        ----------
        generator_code : str
            Generator identifier.
        size : int
            Sample size.

        Returns
        -------
        list[list[float]]
            Stored samples.
        """
        pass

    @abstractmethod
    def get_rvs_stat(self) -> list[tuple[str, int, int]]:
        """
        Get RVS statistics.

        Returns
        -------
        list[tuple[str, int, int]]
            (generator_code, size, count)
        """
        pass

    @abstractmethod
    def clear_all_rvs(self):
        """
        Remove all stored RVS data.

        Returns
        -------
        None
        """
        pass


class ICriticalValueStore(IStore, ABC):
    """Critical value storage interface."""

    @abstractmethod
    def insert_critical_value(self, code: str, size: int, sl: float, value: float | tuple[float, float]):
        """
        Store critical value.

        Parameters
        ----------
        code : str
            Test identifier.
        size : int
            Sample size.
        sl : float
            Significance level.
        value : float | tuple[float, float]
            Critical value.
        """
        pass

    @abstractmethod
    def insert_distribution(self, code: str, size: int, data: list[float]):
        """
        Store distribution data.

        Parameters
        ----------
        code : str
            Test identifier.
        size : int
            Sample size.
        data : list[float]
            Distribution values.
        """
        pass

    @abstractmethod
    def get_critical_value(self, code: str, size: int, sl: float) -> float | tuple[float, float] | None:
        """
        Retrieve critical value.

        Parameters
        ----------
        code : str
            Test identifier.
        size : int
            Sample size.
        sl : float
            Significance level.

        Returns
        -------
        float | tuple[float, float] | None
            Stored value or None.
        """
        pass

    @abstractmethod
    def get_distribution(self, code: str, size: int) -> list[float] | None:
        """
        Retrieve distribution.

        Parameters
        ----------
        code : str
            Test identifier.
        size : int
            Sample size.

        Returns
        -------
        list[float] | None
            Distribution or None.
        """
        pass


class IResultStore(IStore):
    """Result storage interface."""

    @abstractmethod
    def insert_result(self, result_id: str, result: Any):
        """
        Store result.

        Parameters
        ----------
        result_id : str
            Unique identifier.
        result : Any
            Stored object.
        """
        pass

    @abstractmethod
    def get_result(self, result_id: str) -> Any:
        """
        Retrieve result.

        Parameters
        ----------
        result_id : str
            Unique identifier.

        Returns
        -------
        Any
            Stored result.
        """
        pass

    @abstractmethod
    def get_results(self, offset: int, limit: int):  # -> [PowerResultModel]:
        """
        Retrieve paginated results.

        Parameters
        ----------
        offset : int
            Offset.
        limit : int
            Limit.

        Returns
        -------
        list[Any]
            List of results.
        """
        pass


# TODO: refactoring to db_store!!!
