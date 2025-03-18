import csv
from pathlib import Path

from typing_extensions import override

from stattest.persistence.file_store.store import read_json, write_json
from stattest.persistence.models import ICriticalValueStore


class CriticalValueFileStore(ICriticalValueStore):
    csv_delimiter = ";"
    separator = ":"

    def __init__(self, path="test_distribution"):
        super().__init__()
        self.path = path
        self.filename = Path(path, "critical_value.json")
        self.cache = {}

    @override
    def init(self):
        if not Path(self.path).exists():
            Path(self.path).mkdir(parents=True)
        mem_cache = {}
        if Path(self.filename).is_file():
            mem_cache = read_json(self.filename)
        self.cache = mem_cache

    @override
    def insert_critical_value(
        self, code: str, size: int, sl: float, value: float | tuple[float, float]
    ):
        """
        Insert critical value to store.

        :param code: test code
        :param size: rvs size
        :param sl: significant level
        :param value: critical value
        """

        key = self._create_key([code, str(size), str(sl)])
        self.cache[key] = value
        write_json(self.filename, self.cache)

    def insert_distribution(self, code: str, size: int, data: list[float]):
        """
        Save distribution to csv file. Name generated by {test_code}_{size}.scv

        :param code: statistic test code
        :param size: sample size
        :param data: distribution data to save
        """

        file_path = self.__build_file_path(code, size)
        with Path(file_path).open("w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=self.csv_delimiter, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(data)

    def get_critical_value(
        self, code: str, size: int, sl: float
    ) -> tuple[float, float] | float | None:
        """
        Get critical value from store.
        :param code: test code
        :param size: rvs size
        :param sl: significant level
        """

        key = self._create_key([code, str(size), str(sl)])
        if key not in self.cache.keys():
            return None

        return self.cache[key]

    def get_distribution(self, code: str, size: int) -> list[float] | None:
        """
        Return distribution cached value or None.

        :param code: statistic test code
        :param size: sample size
        """

        file_path = self.__build_file_path(code, size)
        if Path(file_path).exists():
            with Path(file_path).open(newline="") as f:
                reader = csv.reader(f, delimiter=self.csv_delimiter, quoting=csv.QUOTE_NONNUMERIC)
                return [float(x) for x in list(reader)[0]]
        else:
            return None

    def __build_file_path(self, test_code: str, size: int):
        file_name = test_code + "_" + str(size) + ".csv"
        return Path(self.path, file_name)

    def _create_key(self, keys: list[str]):
        return self.separator.join(keys)


class ThreadSafeMonteCarloCacheService(CriticalValueFileStore):
    def __init__(
        self,
        lock,
        filename="cache.json",
        separator=":",
        csv_delimiter=";",
        dir_path="test_distribution",
    ):
        super().__init__(filename, separator, csv_delimiter, dir_path)
        self.lock = lock

    def flush(self):
        """
        Flush data to persisted store.
        """

        with self.lock:
            write_json(self.filename, self.cache)

    def put(self, key: str, value):
        """
        Put object to cache.

        :param key: cache key
        :param value: cache value
        """
        with self.lock:
            self.cache[key] = value

    def put_with_level(self, keys: list[str], value):
        """
        Put JSON value by keys chain in 'keys' param.

        :param value: value to put
        :param keys: keys chain param
        """

        key = self._create_key(keys)
        with self.lock:
            self.cache[key] = value
