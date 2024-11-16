from typing import Optional


class IStore:

    def migrate(self):
        """
        Migrate store.
        """
        pass

    def init(self, **kwargs):
        """
        Initialize store.
        :param kwargs: argument for store initialization.
        """
        pass


class IRvsStore(IStore):

    def insert_all_rvs(self, generator_code: str, size: int, data: [[float]]):
        pass

    def insert_rvs(self, generator_code: str, size: int, data: [float]):
        pass

    def get_rvs_count(self, generator_code: str, size: int) -> int:
        pass

    def get_rvs(self, generator_code: str, size: int) -> [float]:
        pass

    def get_rvs_stat(self) -> [(str, int, int)]:
        pass

    def clear_all_rvs(self):
        pass


class ICriticalValueStore(IStore):

    def insert_critical_value(self, code: str, size: int, sl: float, value: float):
        pass

    def insert_distribution(self, code: str, size: int, data: [float]):
        pass

    def get_critical_value(self, code: str, size: int, sl: float) -> Optional[float]:
        pass

    def get_distribution(self, code: str, size: int) -> [float]:
        pass


class IPowerResultStore(IStore):

    def insert_power(self, alpha: float, size: int, test_code: str, alternative_code: str, power: float):
        pass

    def get_power(self, alpha: float, size: int, test_code: str, alternative_code: str) -> Optional[float]:
        pass

    def get_powers(self, offset: int, limit: int):
        pass
