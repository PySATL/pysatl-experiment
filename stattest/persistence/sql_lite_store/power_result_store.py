import sqlite3
from typing import ClassVar

import numpy as np
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, scoped_session, sessionmaker
from typing_extensions import override

from stattest.persistence.models import IPowerResultStore
from stattest.persistence.sql_lite_store import ModelBase
from stattest.persistence.sql_lite_store.base import SessionType
from stattest.persistence.sql_lite_store.db_init import get_request_or_thread_id, init_db


class PowerResultModel(ModelBase):
    """
    Pair Locks database model.
    """

    __tablename__ = "power_result"

    id: Mapped[int] = mapped_column(primary_key=True)
    alpha: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    alternative_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    power: Mapped[float] = mapped_column(Float, nullable=False)


class PowerResultSqlLiteStore(IPowerResultStore):
    session: ClassVar[SessionType]

    def __init__(self):
        super().__init__()

    def init(self, **kwargs):
        sqlite3.register_adapter(np.int64, lambda val: int(val))
        engine = init_db("sqlite:///pysatl.sqlite")
        PowerResultSqlLiteStore.session = scoped_session(
            sessionmaker(bind=engine, autoflush=False),
            scopefunc=get_request_or_thread_id,
        )
        ModelBase.metadata.create_all(engine)

    @override
    def insert_power(
        self,
        alpha: float,
        size: int,
        test_code: str,
        alternative_code: str,
        power: float,
    ):
        data = PowerResultModel(
            alpha=alpha,
            size=size,
            test_code=test_code,
            alternative_code=alternative_code,
            power=power,
        )
        PowerResultSqlLiteStore.session.add(data)
        PowerResultSqlLiteStore.session.commit()

    @override
    def get_power(self, alpha: float, size: int, test_code: str, alternative_code: str) -> float:
        result = (
            PowerResultSqlLiteStore.session.query(PowerResultModel)
            .filter(
                PowerResultModel.alpha == alpha,
                PowerResultModel.test_code == test_code,
                PowerResultModel.size == size,
                PowerResultModel.alternative_code == alternative_code,
            )
            .first()
        )

        if not result:
            return None

        return result.power

    @override
    def get_powers(self, offset: int, limit: int) -> [PowerResultModel]:
        return (
            PowerResultSqlLiteStore.session.query(PowerResultModel)
            .order_by(PowerResultModel.id)
            .offset(offset)
            .limit(limit)
        ).all()
