from typing import ClassVar

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from stattest.persistence.db_store.base import ModelBase, SessionType
from stattest.persistence.db_store.model import AbstractDbStore
from stattest.persistence.models import IBenchmarkResultStore


class BenchmarkResultModel(ModelBase):
    """
    Pair Locks database model.
    """

    __tablename__ = "benchmark_result"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    benchmark: Mapped[str] = mapped_column(String, nullable=False)


class BenchmarkResultDbStore(IBenchmarkResultStore, AbstractDbStore):
    session: ClassVar[SessionType]
    __separator = ";"

    def insert_benchmark(self, test_code: str, size: int, benchmark: [float]):
        """
        Insert benchmark to store.

        :param test_code: test code
        :param benchmark:  benchmark
        """

        data_str = BenchmarkResultDbStore.__separator.join(map(str, benchmark))
        data = BenchmarkResultModel(size=size, test_code=test_code, benchmark=data_str)
        BenchmarkResultDbStore.session.add(data)
        BenchmarkResultDbStore.session.commit()

    def get_benchmark(self, test_code: str, size: int) -> [float]:
        """
        Get benchmark from store.

        :param test_code: test code

        :return: benchmark on None
        """
        result = (
            BenchmarkResultDbStore.session.query(BenchmarkResultModel)
            .filter(BenchmarkResultModel.test_code == test_code, BenchmarkResultModel.size == size)
            .first()
        )

        if not result:
            return []

        return [float(x) for x in result.benchmark.split(BenchmarkResultDbStore.__separator)]

    def get_benchmarks(self, offset: int, limit: int):  # -> [PowerResultModel]:
        """
        Get several powers from store.

        :param offset: offset
        :param limit: limit

        :return: list of PowerResultModel
        """
        result = (
            BenchmarkResultDbStore.session.query(BenchmarkResultModel)
            .order_by(BenchmarkResultModel.id)
            .offset(offset)
            .limit(limit)
        ).all()
        result = [
            BenchmarkResultModel(
                size=b.size,
                test_code=b.test_code,
                benchmark=[float(x) for x in b.benchmark.split(BenchmarkResultDbStore.__separator)],
            )
            for b in result
        ]
        return result
