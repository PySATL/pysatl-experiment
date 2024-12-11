from abc import ABC, abstractmethod
from typing import Optional


class IStore:
    def migrate(self):
        """
        Migrate store.
        """
        pass

    def init(self):
        """
        Initialize store.
        """
        pass


class IRvsStore(IStore, ABC):
    def insert_all_rvs(self, generator_code: str, size: int, data: [[float]]):
        """
        Insert several rvs data to store.
        By default use single rvs insert.

        :param generator_code: generator unique code
        :param size: rvs size
        :param data: list of lists rvs data
        """
        for d in data:
            self.insert_rvs(generator_code, size, d)

    @abstractmethod
    def insert_rvs(self, generator_code: str, size: int, data: [float]):
        """
        Insert one rvs data to store.

        :param generator_code: generator unique code
        :param size: rvs size
        :param data: list of lists rvs data
        """
        pass

    def get_rvs_count(self, generator_code: str, size: int) -> int:
        """
        Get rvs count from store.
        By default use get rvs data.

        :param generator_code: generator unique code
        :param size: rvs size

        Return rvs data count
        """
        return len(self.get_rvs(generator_code, size))

    @abstractmethod
    def get_rvs(self, generator_code: str, size: int) -> [[float]]:
        """
        Get rvs data from store.

        :param generator_code: generator unique code
        :param size: rvs size

        Return list of lists rvs data
        """
        pass

    @abstractmethod
    def get_rvs_stat(self) -> [(str, int, int)]:
        """
        Get rvs data statistics.

        Return list of tuples (generator code, size, count)
        """
        pass

    @abstractmethod
    def clear_all_rvs(self):
        """
        Clear ALL data in store.
        """
        pass


class ICriticalValueStore(IStore, ABC):
    @abstractmethod
    def insert_critical_value(self, code: str, size: int, sl: float, value: float):
        """
        Insert critical value to store.

        :param code: test code
        :param size: rvs size
        :param sl: significant level
        :param value: critical value
        """
        pass

    @abstractmethod
    def insert_distribution(self, code: str, size: int, data: [float]):
        """
        Insert distribution to store.

        :param code: test code
        :param size: rvs size
        :param data: distribution data
        """
        pass

    @abstractmethod
    def get_critical_value(self, code: str, size: int, sl: float) -> Optional[float]:
        """
        Get critical value from store.
        :param code: test code
        :param size: rvs size
        :param sl: significant level
        """
        pass

    @abstractmethod
    def get_distribution(self, code: str, size: int) -> [float]:
        """
        Get distribution from store.

        :param code: test code
        :param size: rvs size
        """
        pass


class IResultStore(IStore):
    @abstractmethod
    def insert_result(self, result_id: str, result: any):
        """
        Insert benchmark to store.

        :param result_id: result id
        :param result: the result
        """
        pass

    @abstractmethod
    def get_result(self, result_id: str) -> any:
        """
        Get benchmark from store.

        :param result_id: result id

        :return: result or None
        """
        pass

    @abstractmethod
    def get_results(self, offset: int, limit: int):  # -> [PowerResultModel]:
        """
        Get several powers from store.

        :param offset: offset
        :param limit: limit

        :return: list of results
        """
        pass
