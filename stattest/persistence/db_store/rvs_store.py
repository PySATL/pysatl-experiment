from typing import ClassVar

from sqlalchemy import Integer, Row, String, func, text
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import override

from stattest.persistence import IRvsStore
from stattest.persistence.db_store.base import ModelBase, SessionType
from stattest.persistence.db_store.model import AbstractDbStore


class RVS(ModelBase):
    """
    RVS data database model.

    """

    __tablename__ = "rvs_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # type: ignore
    size: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # type: ignore
    data: Mapped[str] = mapped_column(String(), nullable=False)  # type: ignore


class RVSStat(ModelBase):
    """
    RVS stat data database model.

    """

    __tablename__ = "rvs_stat"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)  # type: ignore
    size: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
    count: Mapped[int] = mapped_column(Integer)  # type: ignore


class RvsDbStore(AbstractDbStore, IRvsStore):
    session: ClassVar[SessionType]
    __separator = ";"

    @override
    def insert_all_rvs(self, generator_code: str, size: int, data: list[list[float]]):
        if len(data) == 0:
            return

        data_to_insert = [
            {
                "code": generator_code,
                "size": int(size),
                "data": RvsDbStore.__separator.join(map(str, d)),
            }
            for d in data
        ]
        statement = text("INSERT INTO rvs_data (code, size, data) VALUES (:code, :size, :data)")
        RvsDbStore.session.execute(statement, data_to_insert)
        RvsDbStore.session.commit()

    @override
    def insert_rvs(self, code: str, size: int, data: list[float]):
        data_str = RvsDbStore.__separator.join(map(str, data))
        RvsDbStore.session.add(RVS(code=code, size=int(size), data=data_str))
        RvsDbStore.session.commit()

    @override
    def get_rvs_count(self, code: str, size: int):
        data = self.get_rvs(code, size)
        return len(data)

    @override
    def get_rvs(self, code: str, size: int) -> list[list[float]]:
        samples = (
            RvsDbStore.session.query(RVS)
            .filter(
                RVS.code == code,
                RVS.size == size,
            )
            .all()
        )

        if not samples:
            return []

        return [[float(x) for x in sample.data.split(RvsDbStore.__separator)] for sample in samples]

    @override
    def get_rvs_stat(self) -> list[tuple[str, int, int]]:
        query_result: list[Row[tuple[str, int, int]]] = (
            RvsDbStore.session.query(RVS.code, RVS.size, func.count(RVS.code))
            .group_by(RVS.code, RVS.size)
            .all()
        )

        return [tuple(row) for row in query_result]

    @override
    def clear_all_rvs(self):
        RvsDbStore.session.query(RVS).delete()
