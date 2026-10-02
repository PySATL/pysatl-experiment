"""
Time complexity persistence layer (SQLAlchemy implementation).

This module provides database models and storage implementation for
persisting execution time measurements of statistical criteria under
different experiment configurations.

The module ensures uniqueness of stored records via a composite database
constraint and provides CRUD operations for time complexity results.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict
from itertools import islice
from typing import cast

from sqlalchemy import Integer, String, Table, UniqueConstraint, delete, inspect, select
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from pysatl_experiment.persistence.contracts.time_complexity import ITimeComplexityStorage
from pysatl_experiment.persistence.models.bulk import BulkBatch
from pysatl_experiment.persistence.models.time_complexity import (
    TimeComplexityFilter,
    TimeComplexityModel,
    TimeComplexityQuery,
)
from pysatl_experiment.persistence.sqlalchemy.base import ModelBase
from pysatl_experiment.persistence.sqlalchemy.connection import init_db
from pysatl_experiment.persistence.validation import require_positive_integer


class AlchemyTimeComplexity(ModelBase):
    """
    SQLAlchemy ORM model for execution time measurements of statistical criteria under experiment configurations.

    Each row stores timing results for a unique combination of:
        - criterion code and its parameters,
        - sample size,
        - Monte-Carlo repetition count.
        - source sample-series code.

    Uniqueness is enforced via the ``uq_time_complexity_unique`` constraint.

    Attributes
    ----------
    id : int
        Primary key.
    criterion_code : str
        Identifier of the statistical criterion/test.
    criterion_parameters : str
        JSON-serialized parameters of the criterion.
    sample_size : int
        Sample size used in evaluation.
    samples_count : int
        Number of samples/simulations.
    experiment_name : str
        Name of the experiment run.
    results_times : str
        JSON-serialized execution time results.
    generator_code : str
        Source sample-series identifier.

    Notes
    -----
    All structured fields (parameters and results) are stored as JSON strings.
    Consistent serialization is required for correct querying.
    """

    __tablename__ = "time_complexity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
    criterion_code: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    criterion_parameters: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # type: ignore
    samples_count: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # type: ignore
    experiment_name: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    generator_code: Mapped[str] = mapped_column(String, nullable=False, index=True)
    results_times: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "experiment_name",
            "generator_code",
            "criterion_code",
            "criterion_parameters",
            "sample_size",
            "samples_count",
            name="uq_time_complexity_unique",
        ),
    )


class AlchemyTimeComplexityStorage(ITimeComplexityStorage):
    """Store timing results with instance-owned sessions and bounded transactions."""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self._sessions: sessionmaker[Session] | None = None

    def init(self) -> None:
        """Initialize the table and session factory once per instance."""
        if self._sessions is not None:
            return
        engine = init_db(self.db_url)
        try:
            table = cast(Table, AlchemyTimeComplexity.__table__)
            schema = inspect(engine)
            if schema.has_table(table.name) and "generator_code" not in {
                column["name"] for column in schema.get_columns(table.name)
            }:
                raise RuntimeError(
                    "The time_complexity table uses the old schema without generator_code. "
                    "Use a new database and regenerate the experiment, or explicitly migrate "
                    "sample-series codes and the time complexity unique constraint."
                )
            table.create(engine, checkfirst=True)
        except Exception:
            engine.dispose()
            raise
        self._sessions = sessionmaker(bind=engine, expire_on_commit=False)

    def _session_factory(self) -> sessionmaker[Session]:
        if self._sessions is None:
            raise RuntimeError("Storage not initialized. Call init() first.")
        return self._sessions

    @classmethod
    def _conditions(cls, query: TimeComplexityFilter):
        conditions = [AlchemyTimeComplexity.experiment_name == query.experiment_name]
        for name in ("generator_code", "criterion_code", "sample_size", "samples_count"):
            value = getattr(query, name)
            if value is not None:
                conditions.append(getattr(AlchemyTimeComplexity, name) == value)
        if query.criterion_parameters is not None:
            conditions.append(
                AlchemyTimeComplexity.criterion_parameters
                == cls._serialize_criterion_parameters(query.criterion_parameters)
            )
        return conditions

    @classmethod
    def _to_model(cls, row: AlchemyTimeComplexity) -> TimeComplexityModel:
        return TimeComplexityModel(
            experiment_name=row.experiment_name,
            generator_code=row.generator_code,
            criterion_code=row.criterion_code,
            criterion_parameters=cls._normalize_criterion_parameters(json.loads(row.criterion_parameters)),
            sample_size=row.sample_size,
            samples_count=row.samples_count,
            results_times=json.loads(row.results_times),
        )

    def read_bulk(
        self, query: TimeComplexityFilter, *, after_id: int | None = None, batch_size: int = 1000
    ) -> BulkBatch[TimeComplexityModel]:
        """Read one bounded page ordered by the stable database id."""
        require_positive_integer(batch_size, "batch_size")
        conditions = self._conditions(query)
        if after_id is not None:
            require_positive_integer(after_id, "after_id")
            conditions.append(AlchemyTimeComplexity.id > after_id)
        statement = (
            select(AlchemyTimeComplexity).where(*conditions).order_by(AlchemyTimeComplexity.id).limit(batch_size)
        )
        with self._session_factory()() as session:
            rows = session.scalars(statement).all()
            return BulkBatch(
                items=[self._to_model(row) for row in rows],
                next_after_id=rows[-1].id if len(rows) == batch_size else None,
            )

    def bulk_insert(self, data: Iterable[TimeComplexityModel], *, batch_size: int = 1000) -> None:
        """Upsert atomic bounded batches; duplicate keys keep the last result."""
        require_positive_integer(batch_size, "batch_size")
        sessions = self._session_factory()
        source = iter(data)
        while batch := list(islice(source, batch_size)):
            with sessions.begin() as session:
                for model in batch:
                    values = asdict(model)
                    results_times = json.dumps(values.pop("results_times"))
                    query = TimeComplexityFilter(**values)
                    existing = session.scalar(select(AlchemyTimeComplexity).where(*self._conditions(query)))
                    if existing is None:
                        values["criterion_parameters"] = self._serialize_criterion_parameters(
                            model.criterion_parameters
                        )
                        session.add(AlchemyTimeComplexity(**values, results_times=results_times))
                    else:
                        existing.results_times = results_times

    def get_data(self, query: TimeComplexityQuery) -> TimeComplexityModel | None:
        """Read one result by its complete key."""
        batch = self.read_bulk(TimeComplexityFilter(**asdict(query)), batch_size=1)
        return batch.items[0] if batch.items else None

    def insert_data(self, data: TimeComplexityModel) -> None:
        """Upsert one result using the bulk write transaction semantics."""
        self.bulk_insert([data])

    def delete_data(self, query: TimeComplexityQuery) -> None:
        """Delete one result by its complete key."""
        statement = delete(AlchemyTimeComplexity).where(*self._conditions(TimeComplexityFilter(**asdict(query))))
        with self._session_factory().begin() as session:
            session.execute(statement)

    @staticmethod
    def _serialize_criterion_parameters(parameters: dict[str, float]) -> str:
        return json.dumps(AlchemyTimeComplexityStorage._normalize_criterion_parameters(parameters), sort_keys=True)

    @staticmethod
    def _normalize_criterion_parameters(
        parameters: Mapping[str, float] | Sequence[float],
    ) -> dict[str, float]:
        if isinstance(parameters, Mapping):
            return {str(key): value for key, value in sorted(parameters.items(), key=lambda item: str(item[0]))}
        return {str(index): value for index, value in enumerate(parameters)}
