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
from typing import ClassVar

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.pysatl_experiment.persistence.db_store.base import ModelBase, SessionType
from src.pysatl_experiment.persistence.db_store.model import AbstractDbStore
from src.pysatl_experiment.persistence.model.time_complexity import (
    ITimeComplexityStorage,
    TimeComplexityModel,
    TimeComplexityQuery,
)


class AlchemyTimeComplexity(ModelBase):
    """
    SQLAlchemy ORM model for execution time measurements of statistical criteria under experiment configurations.

    Each row stores timing results for a unique combination of:
        - criterion code and its parameters,
        - sample size,
        - Monte-Carlo repetition count.

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
    monte_carlo_count : int
        Number of Monte-Carlo simulations.
    experiment_id : int
        Identifier of the experiment run.
    results_times : str
        JSON-serialized execution time results.

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
    """
    SQLAlchemy-backed storage for time complexity measurements.

    This class provides CRUD operations for storing and retrieving
    execution time measurements of statistical criteria.

    Records are uniquely identified by:
        - criterion_code
        - criterion_parameters (JSON-serialized)
        - sample_size
        - monte_carlo_count

    The storage must be explicitly initialized via :meth:`init`
    before any database operations are performed.

    Attributes
    ----------
    session : ClassVar[SessionType]
        Shared SQLAlchemy session used by all storage instances.
    _initialized : bool
        Indicates whether storage has been initialized.
    """

    session: ClassVar[SessionType]

    def __init__(self, db_url: str):
        """
        Initialize time complexity storage.

        Parameters
        ----------
        db_url : str
            SQLAlchemy database connection string.

        Notes
        -----
        The constructor does not create DB connection immediately.
        Call :meth:`init` to initialize the storage.
        """
        super().__init__(db_url=db_url)
        self._initialized: bool = False

    def init(self) -> None:
        """
        Initialize database engine and SQLAlchemy session.

        This method must be called before using any CRUD operations.

        Side Effects
        ------------
        - Creates database schema (if not exists)
        - Initializes session factory
        - Sets internal initialization flag
        """
        super().init()
        self._initialized = True

    def _get_session(self) -> SessionType:
        """
        Return active SQLAlchemy session.

        Returns
        -------
        SessionType
            Active DB session.

        Raises
        ------
        RuntimeError
            If storage was not initialized via :meth:`init`.

        Notes
        -----
        Session is stored at class level (shared across instances).
        """
        if not getattr(self, "_initialized", False):
            raise RuntimeError("Storage not initialized. Call init() first.")
        return AlchemyTimeComplexityStorage.session

    def get_data(self, query: TimeComplexityQuery) -> TimeComplexityModel | None:
        """
        Retrieve stored time complexity result matching query parameters.

        Parameters
        ----------
        query : TimeComplexityQuery
            Query defining:
                - criterion configuration
                - sample size
                - Monte-Carlo count

        Returns
        -------
        TimeComplexityModel | None
            Matched record or None if not found.

        Notes
        -----
        Matching is strict and relies on JSON-serialized parameter equality.
        """
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

    def insert_data(self, data: TimeComplexityModel) -> None:
        """
        Insert or update a time complexity record.

        If a record with the same composite key exists, it is updated.
        Otherwise, a new record is created.

        Parameters
        ----------
        data : TimeComplexityModel
            Time complexity measurement to store.

        Notes
        -----
        - Existing records update:
            - experiment_id
            - results_times
        - criterion_parameters and results_times are JSON-serialized.
        """
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

    def delete_data(self, query: TimeComplexityQuery) -> None:
        """
        Delete time complexity record matching query.

        Parameters
        ----------
        query : TimeComplexityQuery
            Key identifying record to delete.

        Notes
        -----
        Operation is no-op if record does not exist.
        Matching is strict (exact JSON + numeric equality).
        """
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
