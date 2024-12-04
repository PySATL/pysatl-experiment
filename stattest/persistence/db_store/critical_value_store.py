from typing import ClassVar, Optional

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import override

from stattest.persistence.db_store.base import ModelBase, SessionType
from stattest.persistence.db_store.model import AbstractDbStore
from stattest.persistence.models import ICriticalValueStore


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


class CriticalValueDbStore(AbstractDbStore, ICriticalValueStore):
    session: ClassVar[SessionType]
    __separator = ";"

    @override
    def insert_critical_value(self, code: str, size: int, sl: float, value: float):
        CriticalValueDbStore.session.add(
            CriticalValue(code=code, sl=sl, size=int(size), value=value)
        )
        CriticalValueDbStore.session.commit()

    @override
    def insert_distribution(self, code: str, size: int, data: [float]):
        data_to_insert = CriticalValueDbStore.__separator.join(map(str, data))
        CriticalValueDbStore.session.add(
            Distribution(code=code, size=int(size), data=data_to_insert)
        )
        CriticalValueDbStore.session.commit()

    @override
    def get_critical_value(self, code: str, size: int, sl: float) -> Optional[float]:
        critical_value = CriticalValueDbStore.session.query(CriticalValue).get((code, size, sl))
        if critical_value is not None:
            return critical_value.value

    @override
    def get_distribution(self, code: str, size: int) -> [float]:
        distribution = CriticalValueDbStore.session.query(Distribution).get((code, size))
        if distribution is not None:
            return [float(x) for x in distribution.data.split(CriticalValueDbStore.__separator)]
