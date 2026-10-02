"""SQLAlchemy storage for experiment-owned samples with bounded batch operations."""

import json
from collections.abc import Iterable
from itertools import islice
from typing import cast

from pysatl_criterion.persistence.sqlalchemy.alchemy_decorator import CompressedFloatArray
from sqlalchemy import CheckConstraint, Index, Integer, String, Table, delete, func, insert, select
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.models.random_values import (
    RandomValuesBatch,
    RandomValuesFilter,
    RandomValuesModel,
)
from pysatl_experiment.persistence.sqlalchemy.base import ModelBase
from pysatl_experiment.persistence.sqlalchemy.connection import init_db
from pysatl_experiment.persistence.validation import require_positive_integer


class AlchemyRandomValues(ModelBase):
    """One row per sample; id is a technical reading position, not a sample number."""

    __tablename__ = "random_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_name: Mapped[str] = mapped_column(String, nullable=False)
    generator_code: Mapped[str] = mapped_column(String, nullable=False)
    generator_parameters: Mapped[str] = mapped_column(String, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[list[float]] = mapped_column(CompressedFloatArray(), nullable=False)

    __table_args__ = (
        CheckConstraint("length(trim(experiment_name)) > 0", name="ck_random_values_experiment"),
        CheckConstraint("length(trim(generator_code)) > 0", name="ck_random_values_generator"),
        CheckConstraint("sample_size > 0", name="ck_random_values_size"),
        Index("ix_random_values_experiment_position", "experiment_name", "id"),
        Index("ix_random_values_experiment_generator_size", "experiment_name", "generator_code", "sample_size", "id"),
    )


class AlchemyRandomValuesStorage(IRandomValuesStorage):
    """Use an instance-owned session factory and close each operation's transaction."""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self._sessions: sessionmaker[Session] | None = None

    def init(self) -> None:
        """Initialize the sample table and the session factory."""
        if self._sessions is not None:
            return
        engine = init_db(self.db_url)
        try:
            cast(Table, AlchemyRandomValues.__table__).create(engine, checkfirst=True)
        except Exception:
            engine.dispose()
            raise
        self._sessions = sessionmaker(bind=engine, expire_on_commit=False)

    def _session_factory(self) -> sessionmaker[Session]:
        if self._sessions is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        return self._sessions

    @staticmethod
    def _conditions(query: RandomValuesFilter):
        conditions = [AlchemyRandomValues.experiment_name == query.experiment_name]
        if query.generator_code is not None:
            conditions.append(AlchemyRandomValues.generator_code == query.generator_code)
        if query.sample_size is not None:
            conditions.append(AlchemyRandomValues.sample_size == query.sample_size)
        return conditions

    @staticmethod
    def _to_model(row: AlchemyRandomValues) -> RandomValuesModel:
        return RandomValuesModel(
            experiment_name=row.experiment_name,
            generator_code=row.generator_code,
            generator_parameters=json.loads(row.generator_parameters),
            sample_size=row.sample_size,
            data=row.data,
        )

    def bulk_insert(self, data: Iterable[RandomValuesModel], *, batch_size: int = 1000) -> None:
        """Append using bulk INSERT and one transaction per bounded input batch."""
        require_positive_integer(batch_size, "batch_size")
        sessions = self._session_factory()
        source = iter(data)
        while batch := list(islice(source, batch_size)):
            records = []
            for sample in batch:
                # Models contain mutable data; recheck before writing.
                sample.__post_init__()
                records.append(
                    dict(
                        experiment_name=sample.experiment_name,
                        generator_code=sample.generator_code,
                        generator_parameters=json.dumps(sample.generator_parameters),
                        sample_size=sample.sample_size,
                        data=sample.data,
                    )
                )
            with sessions.begin() as session:
                session.execute(insert(AlchemyRandomValues), records)

    def read_bulk(
        self, query: RandomValuesFilter, *, after_id: int | None = None, batch_size: int = 1000
    ) -> RandomValuesBatch:
        """Read one page; a full final page may require one further empty read."""
        require_positive_integer(batch_size, "batch_size")
        conditions = self._conditions(query)
        if after_id is not None:
            require_positive_integer(after_id, "after_id")
            conditions.append(AlchemyRandomValues.id > after_id)
        statement = select(AlchemyRandomValues).where(*conditions).order_by(AlchemyRandomValues.id).limit(batch_size)
        with self._session_factory()() as session:
            rows = session.scalars(statement).all()
            return RandomValuesBatch(
                items=[self._to_model(row) for row in rows],
                next_after_id=rows[-1].id if len(rows) == batch_size else None,
            )

    def count(self, query: RandomValuesFilter) -> int:
        """Count samples using the same filters as reading and deletion."""
        statement = select(func.count()).select_from(AlchemyRandomValues).where(*self._conditions(query))
        with self._session_factory()() as session:
            return session.execute(statement).scalar_one()

    def delete(self, query: RandomValuesFilter) -> int:
        """Delete only matching rows of the named experiment, in one transaction."""
        statement = delete(AlchemyRandomValues).where(*self._conditions(query))
        with self._session_factory().begin() as session:
            result = session.connection().execute(statement)
            return result.rowcount
