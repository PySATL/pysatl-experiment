from typing import ClassVar

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import override

from stattest.persistence.db_store.model import AbstractDbStore
from stattest.persistence.models import IPowerResultStore
from stattest.persistence.db_store import ModelBase
from stattest.persistence.db_store.base import SessionType


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


class PowerResultDbStore(IPowerResultStore, AbstractDbStore):
    session: ClassVar[SessionType]

    @override
    def insert_power(self, alpha: float, size: int, test_code: str, alternative_code: str, power: float):
        data = PowerResultModel(alpha=alpha, size=size, test_code=test_code, alternative_code=alternative_code,
                                power=power)
        PowerResultDbStore.session.add(data)
        PowerResultDbStore.session.commit()

    @override
    def get_power(self, alpha: float, size: int, test_code: str, alternative_code: str) -> float:
        result = PowerResultDbStore.session.query(PowerResultModel).filter(
            PowerResultModel.alpha == alpha, PowerResultModel.test_code == test_code,
            PowerResultModel.size == size, PowerResultModel.alternative_code == alternative_code,
        ).first()

        if not result:
            return None

        return result.power

    @override
    def get_powers(self, offset: int, limit: int) -> [PowerResultModel]:
        return (PowerResultDbStore.session.query(PowerResultModel)
                .order_by(PowerResultModel.id).offset(offset).limit(limit)).all()
