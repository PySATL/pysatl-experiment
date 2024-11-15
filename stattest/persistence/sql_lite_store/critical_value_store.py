import sqlite3

import numpy as np
from typing_extensions import override, Optional

from typing import ClassVar

from sqlalchemy.orm import Mapped, mapped_column, scoped_session, sessionmaker
from sqlalchemy import (
    Integer,
    String,
    Float,
)

from stattest.persistence.models import ICriticalValueStore
from stattest.persistence.sql_lite_store.base import ModelBase, SessionType
from stattest.persistence.sql_lite_store.db_init import init_db, get_request_or_thread_id


class Distribution(ModelBase):
    """
    Distribution data database model.

    """

    __tablename__ = "distribution"
    code: Mapped[str] = mapped_column(String(50), primary_key=True)  # type: ignore
    size: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
    data: Mapped[str] = mapped_column(String(), nullable=False)  # type: ignore


class CriticalValue(ModelBase):
    """
    Critical value data database model.

    """

    __tablename__ = "critical_value"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)  # type: ignore
    size: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
    sl: Mapped[float] = mapped_column(Integer, primary_key=True)  # type: ignore
    value: Mapped[float] = mapped_column(Float(), nullable=False)  # type: ignore


class CriticalValueSqLiteStore(ICriticalValueStore):
    session: ClassVar[SessionType]
    __separator = ';'

    def __init__(self, name='pysatl.sqlite'):
        super().__init__()
        self.name = name

    @override
    def init(self):
        sqlite3.register_adapter(np.int64, lambda val: int(val))
        engine = init_db("sqlite:///" + self.name)
        CriticalValueSqLiteStore.session = scoped_session(
            sessionmaker(bind=engine, autoflush=False), scopefunc=get_request_or_thread_id
        )
        ModelBase.metadata.create_all(engine)

    @override
    def insert_critical_value(self, code: str, size: int, sl: float, value: float):
        CriticalValueSqLiteStore.session.add(CriticalValue(code=code, sl=sl, size=int(size), value=value))
        CriticalValueSqLiteStore.session.commit()

    @override
    def insert_distribution(self, code: str, size: int, data: [float]):
        data_to_insert = CriticalValueSqLiteStore.__separator.join(map(str, data))
        CriticalValueSqLiteStore.session.add(Distribution(code=code, size=int(size), data=data_to_insert))
        CriticalValueSqLiteStore.session.commit()

    @override
    def get_critical_value(self, code: str, size: int, sl: float) -> Optional[float]:
        critical_value = CriticalValueSqLiteStore.session.query(CriticalValue).get((code, size, sl))
        if critical_value is not None:
            return critical_value.value

    @override
    def get_distribution(self, code: str, size: int) -> [float]:
        distribution = CriticalValueSqLiteStore.session.query(Distribution).get((code, size))
        if distribution is not None:
            return [float(x) for x in distribution.data.split(CriticalValueSqLiteStore.__separator)]
