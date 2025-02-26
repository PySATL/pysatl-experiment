from typing import ClassVar, List, Optional, Tuple, Union

from sqlalchemy import Float, Integer, String
from sqlalchemy.exc import IntegrityError
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
    sl: Mapped[float] = mapped_column(Float, primary_key=True)  # type: ignore
    lower_value: Mapped[float] = mapped_column(Float, nullable=True)
    upper_value: Mapped[float] = mapped_column(Float, nullable=True)


class CriticalValueDbStore(AbstractDbStore, ICriticalValueStore):
    session: ClassVar[SessionType]
    __separator = ";"

    @override
    def insert_critical_value(
        self, code: str, size: int, sl: float, value: Union[float, Tuple[float, float]]
    ):
        if isinstance(value, tuple):
            lower_value, upper_value = value
        else:
            lower_value, upper_value = value, None

        try:
            CriticalValueDbStore.session.add(
                CriticalValue(
                    code=code,
                    size=int(size),
                    sl=sl,
                    lower_value=lower_value,
                    upper_value=upper_value,
                )
            )
            CriticalValueDbStore.session.commit()
        except IntegrityError:
            CriticalValueDbStore.session.rollback()

    @override
    def insert_distribution(self, code: str, size: int, data: List[float]):
        data_to_insert = CriticalValueDbStore.__separator.join(map(str, data))
        try:
            CriticalValueDbStore.session.add(
                Distribution(code=code, size=int(size), data=data_to_insert)
            )
            CriticalValueDbStore.session.commit()
        except IntegrityError:
            CriticalValueDbStore.session.rollback()

    @override
    def get_critical_value(
        self, code: str, size: int, sl: float
    ) -> Optional[Union[float, Tuple[float, float]]]:
        critical_value = CriticalValueDbStore.session.get(CriticalValue, (code, size, sl))
        if critical_value is not None:
            if critical_value.upper_value is not None:
                return critical_value.lower_value, critical_value.upper_value
            else:
                return critical_value.lower_value
        else:
            return None

    @override
    def get_distribution(self, code: str, size: int) -> Optional[List[float]]:
        distribution = CriticalValueDbStore.session.get(Distribution, (code, size))
        if distribution is not None:
            return [float(x) for x in distribution.data.split(CriticalValueDbStore.__separator)]
        else:
            return None
