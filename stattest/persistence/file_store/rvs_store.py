import csv
import os
import shutil
from pathlib import Path

from typing_extensions import override

from stattest.persistence.models import IRvsStore


class RvsFileStore(IRvsStore):
    __separator = ";"
    __file_separator = "_"

    def __init__(self, path="data"):
        super().__init__()
        self.path = path

    @override
    def init(self):
        if not Path(self.path).exists():
            Path(self.path).mkdir(parents=True)

    @override
    def insert_all_rvs(self, generator_code: str, size: int, data: list[list[float]]):
        file_path = Path(self.path, RvsFileStore.build_rvs_file_name(generator_code, size) + ".csv")
        with Path(file_path).open("w", newline="") as csvfile:
            writer = csv.writer(
                csvfile,
                delimiter=RvsFileStore.__separator,
                quoting=csv.QUOTE_NONNUMERIC,
            )
            writer.writerows(data)

    @override
    def get_rvs_stat(self):
        filenames = next(os.walk(self.path), (None, None, []))[2]  # [] if no file
        result = []
        for filename in filenames:
            rvs_code, size = RvsFileStore.parse_rvs_file_name(filename)
            file_path = Path(self.path, RvsFileStore.build_rvs_file_name(rvs_code, size) + ".csv")
            with Path(file_path).open(newline="") as f:
                reader = csv.reader(
                    f, delimiter=RvsFileStore.__separator, quoting=csv.QUOTE_NONNUMERIC
                )
                result.append((rvs_code, size, len(list(reader))))

        return result

    @override
    def insert_rvs(self, code: str, size: int, data: list[float]):
        file_path = Path(self.path, RvsFileStore.build_rvs_file_name(code, size) + ".csv")
        with Path(file_path).open("w", newline="") as csvfile:
            writer = csv.writer(
                csvfile,
                delimiter=RvsFileStore.__separator,
                quoting=csv.QUOTE_NONNUMERIC,
            )
            writer.writerow(data)

    @override
    def get_rvs_count(self, code: str, size: int) -> int:
        data = self.get_rvs(code, size)
        if data is None:
            return 0
        return len(data)

    @override
    def get_rvs(self, code: str, size: int) -> list[list[float]]:
        file_path = Path(self.path, RvsFileStore.build_rvs_file_name(code, size) + ".csv")
        if not Path(file_path).exists():
            return []
        with Path(file_path).open(newline="") as f:
            reader = csv.reader(f, delimiter=RvsFileStore.__separator, quoting=csv.QUOTE_NONNUMERIC)
            return [[float(x) for x in e] for e in reader]

    @override
    def clear_all_rvs(self):
        shutil.rmtree(self.path)

    @staticmethod
    def parse_rvs_file_name(name: str) -> tuple:
        split = name.split(RvsFileStore.__file_separator)
        size = int(split[-2])
        return RvsFileStore.__file_separator.join(split[:-2]), size

    @staticmethod
    def build_rvs_file_name(generator_code: str, size: int) -> str:
        return (
            generator_code
            + RvsFileStore.__file_separator
            + str(size)
            + RvsFileStore.__file_separator
        )
