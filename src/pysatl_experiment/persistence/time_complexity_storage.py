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
from typing import ClassVar

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from pysatl_experiment.configuration.models.parameters import NumericParameters
from pysatl_experiment.persistence.db_store.base import ModelBase, SessionType
from pysatl_experiment.persistence.db_store.model import AbstractDbStore
from pysatl_experiment.persistence.models.time_complexity import (
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
    samples_count : int
        Number of samples/simulations.
    experiment_name : str
        Name of the experiment run.
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
    samples_count: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # type: ignore
    experiment_name: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    results_times: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "experiment_name",
            "criterion_code",
            "criterion_parameters",
            "sample_size",
            "samples_count",
            name="uq_time_complexity_unique",
        ),
    )


class AlchemyTimeComplexityStorage(AbstractDbStore, ITimeComplexityStorage):
    """
    SQLAlchemy-backed storage for time complexity measurements.

    This class provides CRUD operations for storing and retrieving
    execution time measurements of statistical criteria.

    Records are uniquely identified by:
        - experiment_name
        - criterion_code
        - criterion_parameters (JSON-serialized)
        - sample_size
        - samples_count

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
                - samples count

        Returns
        -------
        TimeComplexityModel | None
            Matched record or None if not found.

        Notes
        -----
        Matching is strict and relies on JSON-serialized parameter equality.
        """
        params_json = self._serialize_criterion_parameters(query.criterion_parameters)
        row: AlchemyTimeComplexity | None = (
            self._get_session()
            .query(AlchemyTimeComplexity)
            .filter(
                AlchemyTimeComplexity.experiment_name == query.experiment_name,
                AlchemyTimeComplexity.criterion_code == query.criterion_code,
                AlchemyTimeComplexity.criterion_parameters == params_json,
                AlchemyTimeComplexity.sample_size == int(query.sample_size),
                AlchemyTimeComplexity.samples_count == int(query.samples_count),
            )
            .one_or_none()
        )
        if row is None:
            return None
        return TimeComplexityModel(
            experiment_name=row.experiment_name,
            criterion_code=query.criterion_code,
            criterion_parameters=self._normalize_criterion_parameters(json.loads(row.criterion_parameters)),
            sample_size=query.sample_size,
            samples_count=query.samples_count,
            results_times=json.loads(row.results_times),
        )

    def _upsert_data(self, data: TimeComplexityModel) -> None:
        params_json = self._serialize_criterion_parameters(data.criterion_parameters)
        existing: AlchemyTimeComplexity | None = (
            self._get_session()
            .query(AlchemyTimeComplexity)
            .filter(
                AlchemyTimeComplexity.experiment_name == data.experiment_name,
                AlchemyTimeComplexity.criterion_code == data.criterion_code,
                AlchemyTimeComplexity.criterion_parameters == params_json,
                AlchemyTimeComplexity.sample_size == int(data.sample_size),
                AlchemyTimeComplexity.samples_count == int(data.samples_count),
            )
            .one_or_none()
        )
        if existing is None:
            entity = AlchemyTimeComplexity(
                criterion_code=data.criterion_code,
                criterion_parameters=params_json,
                sample_size=int(data.sample_size),
                samples_count=int(data.samples_count),
                experiment_name=data.experiment_name,
                results_times=json.dumps(data.results_times),
            )
            self._get_session().add(entity)
        else:
            existing.results_times = json.dumps(data.results_times)

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
            - results_times
        - criterion_parameters and results_times are JSON-serialized.
        """
        self._upsert_data(data)
        self._get_session().commit()

    def bulk_insert_data(self, data_list: Iterable[TimeComplexityModel]) -> None:
        """
        Insert or update multiple time complexity records.

        Parameters
        ----------
        data_list : Iterable[TimeComplexityModel]
            Time complexity measurements to store.

        Notes
        -----
        Uses the same UPSERT-like behavior as :meth:`insert_data`, but
        commits once after all records are processed.
        """
        for data in data_list:
            self._upsert_data(data)
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
        params_json = self._serialize_criterion_parameters(query.criterion_parameters)
        (
            self._get_session()
            .query(AlchemyTimeComplexity)
            .filter(
                AlchemyTimeComplexity.experiment_name == query.experiment_name,
                AlchemyTimeComplexity.criterion_code == query.criterion_code,
                AlchemyTimeComplexity.criterion_parameters == params_json,
                AlchemyTimeComplexity.sample_size == int(query.sample_size),
                AlchemyTimeComplexity.samples_count == int(query.samples_count),
            )
            .delete()
        )
        self._get_session().commit()

    @staticmethod
    def _serialize_criterion_parameters(parameters: NumericParameters) -> str:
        return json.dumps(AlchemyTimeComplexityStorage._normalize_criterion_parameters(parameters), sort_keys=True)

    @staticmethod
    def _normalize_criterion_parameters(
        parameters: Mapping[str, float] | Sequence[float],
    ) -> dict[str, float]:
        if isinstance(parameters, Mapping):
            return {str(key): value for key, value in sorted(parameters.items(), key=lambda item: str(item[0]))}
        return {str(index): value for index, value in enumerate(parameters)}
