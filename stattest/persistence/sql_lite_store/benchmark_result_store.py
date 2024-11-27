import sqlite3
from typing import ClassVar

import numpy as np
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, scoped_session

from stattest.persistence.models import IBenchmarkResultStore
from stattest.persistence.sql_lite_store import ModelBase, init_db, get_request_or_thread_id, SessionType


class BenchmarkResultModel(ModelBase):
    """
    Pair Locks database model.
    """
    __tablename__ = "benchmark_result"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    benchmark: Mapped[str] = mapped_column(String, nullable=False)


class BenchmarkResultSqLiteStore(IBenchmarkResultStore):
    session: ClassVar[SessionType]
    __separator = ';'

    def __init__(self, name='pysatl.sqlite'):
        super().__init__()
        self.name = name

    def init(self, **kwargs):
        sqlite3.register_adapter(np.int64, lambda val: int(val))
        engine = init_db("sqlite:///" + self.name)
        BenchmarkResultSqLiteStore.session = scoped_session(
            sessionmaker(bind=engine, autoflush=False), scopefunc=get_request_or_thread_id
        )
        ModelBase.metadata.create_all(engine)

    def insert_benchmark(self, test_code: str, size: int, benchmark: [float]):
        """
        Insert benchmark to store.

        :param test_code: test code
        :param benchmark:  benchmark
        """

        data_str = BenchmarkResultSqLiteStore.__separator.join(map(str, benchmark))
        data = BenchmarkResultModel(size=size, test_code=test_code, benchmark=data_str)
        BenchmarkResultSqLiteStore.session.add(data)
        BenchmarkResultSqLiteStore.session.commit()

    def get_benchmark(self, test_code: str, size: int) -> [float]:
        """
        Get benchmark from store.

        :param test_code: test code

        :return: benchmark on None
        """
        result = BenchmarkResultSqLiteStore.session.query(BenchmarkResultModel).filter(
            BenchmarkResultModel.test_code == test_code,
            BenchmarkResultModel.size == size
        ).first()

        if not result:
            return []

        return [float(x) for x in result.benchmark.split(BenchmarkResultSqLiteStore.__separator)]

    def get_benchmarks(self, offset: int, limit: int):  # -> [PowerResultModel]:
        """
        Get several powers from store.

        :param offset: offset
        :param limit: limit

        :return: list of PowerResultModel
        """
        result = (BenchmarkResultSqLiteStore.session.query(BenchmarkResultModel)
                  .order_by(BenchmarkResultModel.id).offset(offset).limit(limit)).all()
        result = [
            BenchmarkResultModel(size=b.size, test_code=b.test_code, benchmark=[float(x) for x in b.benchmark.split(
                BenchmarkResultSqLiteStore.__separator)]) for b in result]
        return result
