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


class IRvsStore(IStore):
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

    def get_rvs(self, generator_code: str, size: int) -> [[float]]:
        """
        Get rvs data from store.

        :param generator_code: generator unique code
        :param size: rvs size

        Return list of lists rvs data
        """
        pass

    def get_rvs_stat(self) -> [(str, int, int)]:
        """
        Get rvs data statistics.

        Return list of tuples (generator code, size, count)
        """
        pass

    def clear_all_rvs(self):
        """
        Clear ALL data in store.
        """
        pass


class ICriticalValueStore(IStore):
    def insert_critical_value(self, code: str, size: int, sl: float, value: float):
        """
        Insert critical value to store.

        :param code: test code
        :param size: rvs size
        :param sl: significant level
        :param value: critical value
        """
        pass

    def insert_distribution(self, code: str, size: int, data: [float]):
        """
        Insert distribution to store.

        :param code: test code
        :param size: rvs size
        :param data: distribution data
        """
        pass

    def get_critical_value(self, code: str, size: int, sl: float) -> Optional[float]:
        """
        Get critical value from store.
        :param code: test code
        :param size: rvs size
        :param sl: significant level
        """
        pass

    def get_distribution(self, code: str, size: int) -> [float]:
        """
        Get distribution from store.

        :param code: test code
        :param size: rvs size
        """
        pass


class IPowerResultStore(IStore):
    def insert_power(
        self, sl: float, size: int, test_code: str, alternative_code: str, power: float
    ):
        """
        Insert power to store.

        :param sl: significant level
        :param size: rvs size
        :param test_code: test code
        :param alternative_code:  alternative code
        :param power: test power
        """
        pass

    def get_power(
        self, sl: float, size: int, test_code: str, alternative_code: str
    ) -> Optional[float]:
        """
        Get power from store.

        :param sl: significant level
        :param size: rvs size
        :param test_code: test code
        :param alternative_code: alternative code

        :return: power on None
        """
        pass

    def get_powers(self, offset: int, limit: int):  # -> [PowerResultModel]:
        """
        Get several powers from store.

        :param offset: offset
        :param limit: limit

        :return: list of PowerResultModel
        """
        pass


class IBenchmarkResultStore(IStore):
    def insert_benchmark(self, test_code: str, size: int, benchmark: [float]):
        """
        Insert benchmark to store.

        :param test_code: test code
        :param benchmark:  benchmark
        """
        pass

    def get_benchmark(self, test_code: str, size: int) -> [float]:
        """
        Get benchmark from store.

        :param test_code: test code

        :return: benchmark on None
        """
        pass

    def get_benchmarks(self, offset: int, limit: int):  # -> [PowerResultModel]:
        """
        Get several powers from store.

        :param offset: offset
        :param limit: limit

        :return: list of PowerResultModel
        """
        pass
