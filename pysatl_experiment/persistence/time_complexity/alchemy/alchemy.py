from __future__ import annotations

import json
from typing import ClassVar

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import override

from pysatl_experiment.persistence.db_store.base import ModelBase, SessionType
from pysatl_experiment.persistence.db_store.model import AbstractDbStore
from pysatl_experiment.persistence.model.time_complexity.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityModel,
    TimeComplexityQuery,
)


class AlchemyTimeComplexity(ModelBase):
    __tablename__ = "time_complexity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
    criterion_code: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    criterion_parameters: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # type: ignore
    monte_carlo_count: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # type: ignore
    experiment_id: Mapped[int] = mapped_column(Integer, nullable=False)  # type: ignore
    results_times: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "criterion_code",
            "criterion_parameters",
            "sample_size",
            "monte_carlo_count",
            name="uq_time_complexity_unique",
        ),
    )


class AlchemyTimeComplexityStorage(AbstractDbStore, ITimeComplexityStorage):
    session: ClassVar[SessionType]

    def __init__(self, db_url: str):
        super().__init__(db_url=db_url)
        self._initialized: bool = False

    @override
    def init(self) -> None:
        super().init()
        self._initialized = True

    def _get_session(self) -> SessionType:
        if not getattr(self, "_initialized", False):
            raise RuntimeError("Storage not initialized. Call init() first.")
        return AlchemyTimeComplexityStorage.session

    @override
    def get_data(self, query: TimeComplexityQuery) -> TimeComplexityModel | None:
        params_json = json.dumps(query.criterion_parameters)
        row: AlchemyTimeComplexity | None = (
            self._get_session()
            .query(AlchemyTimeComplexity)
            .filter(
                AlchemyTimeComplexity.criterion_code == query.criterion_code,
                AlchemyTimeComplexity.criterion_parameters == params_json,
                AlchemyTimeComplexity.sample_size == int(query.sample_size),
                AlchemyTimeComplexity.monte_carlo_count == int(query.monte_carlo_count),
            )
            .one_or_none()
        )
        if row is None:
            return None
        return TimeComplexityModel(
            experiment_id=int(row.experiment_id),
            criterion_code=query.criterion_code,
            criterion_parameters=query.criterion_parameters,
            sample_size=query.sample_size,
            monte_carlo_count=query.monte_carlo_count,
            results_times=json.loads(row.results_times),
        )

    @override
    def insert_data(self, data: TimeComplexityModel) -> None:
        params_json = json.dumps(data.criterion_parameters)
        existing: AlchemyTimeComplexity | None = (
            self._get_session()
            .query(AlchemyTimeComplexity)
            .filter(
                AlchemyTimeComplexity.criterion_code == data.criterion_code,
                AlchemyTimeComplexity.criterion_parameters == params_json,
                AlchemyTimeComplexity.sample_size == int(data.sample_size),
                AlchemyTimeComplexity.monte_carlo_count == int(data.monte_carlo_count),
            )
            .one_or_none()
        )
        if existing is None:
            entity = AlchemyTimeComplexity(
                criterion_code=data.criterion_code,
                criterion_parameters=params_json,
                sample_size=int(data.sample_size),
                monte_carlo_count=int(data.monte_carlo_count),
                experiment_id=int(data.experiment_id),
                results_times=json.dumps(data.results_times),
            )
            self._get_session().add(entity)
        else:
            # replace experiment_id and results_times for the unique key
            existing.experiment_id = int(data.experiment_id)
            existing.results_times = json.dumps(data.results_times)
        self._get_session().commit()

    @override
    def delete_data(self, query: TimeComplexityQuery) -> None:
        params_json = json.dumps(query.criterion_parameters)
        (
            self._get_session()
            .query(AlchemyTimeComplexity)
            .filter(
                AlchemyTimeComplexity.criterion_code == query.criterion_code,
                AlchemyTimeComplexity.criterion_parameters == params_json,
                AlchemyTimeComplexity.sample_size == int(query.sample_size),
                AlchemyTimeComplexity.monte_carlo_count == int(query.monte_carlo_count),
            )
            .delete()
        )
        self._get_session().commit()
