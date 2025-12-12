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
    """
    SQLAlchemy ORM model representing measured time complexity results
    for a statistical criterion within an experiment.

    This table stores execution time metrics for running a criterion with
    specific parameters, sample size, and Monte-Carlo iterations.
    Each unique combination of criterion configuration and Monte-Carlo count
    is stored exactly once, enforced by a unique constraint.

    Attributes
    ----------
    id : int
        Primary key of the record.
    criterion_code : str
        Identifier of the statistical criterion (e.g., "KS", "SHAPIRO").
        Used to group results by criterion type.
    criterion_parameters : str
        Serialized parameters of the criterion (e.g., JSON string).
    sample_size : int
        Number of samples used when computing the time complexity.
    monte_carlo_count : int
        Number of Monte-Carlo iterations used to compute time metrics.
    experiment_id : int
        Identifier of the experiment this result belongs to.
    results_times : str
        Serialized execution time results (e.g., JSON or CSV string)
        representing time measurements for each Monte-Carlo run.

    Notes
    -----
    Unique constraint `uq_time_complexity_unique` guarantees uniqueness of
    time complexity data for a specific combination of:

    - criterion_code
    - criterion_parameters
    - sample_size
    - monte_carlo_count
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
    Storage implementation for time-complexity measurement data using SQLAlchemy.

    This class provides persistent storage for `TimeComplexityModel` objects and
    exposes CRUD-style operations for querying, inserting, and deleting
    time-complexity results. It relies on the `AlchemyTimeComplexity` ORM model
    and a lazily initialized SQLAlchemy session.

    The storage must be initialized explicitly via :meth:`init` before use.
    Attempts to read or write data without initialization will raise a
    `RuntimeError`.

    Parameters
    ----------
    db_url : str
        SQLAlchemy database connection string.

    Attributes
    ----------
    session : ClassVar[SessionType]
        Shared SQLAlchemy session used by this storage.
    _initialized : bool
        Indicates whether the storage was initialized via :meth:`init`.

    Methods
    -------
    init() -> None
        Initializes the database (tables, engine, session). Must be called
        before performing operations.
    get_data(query: TimeComplexityQuery) -> TimeComplexityModel | None
        Retrieves a single time-complexity record matching the query criteria.
    insert_data(data: TimeComplexityModel) -> None
        Inserts a new record or updates an existing one matching the unique
        constraint of the ORM entity.
    delete_data(query: TimeComplexityQuery) -> None
        Removes a record that matches the query criteria.

    Notes
    -----
    The unique key for identifying a time-complexity record consists of:
        - criterion_code
        - criterion_parameters (serialized JSON)
        - sample_size
        - monte_carlo_count

    The storage transparently serializes and deserializes complex objects
    (criterion parameters and timing results) using JSON.
    """

    session: ClassVar[SessionType]

    def __init__(self, db_url: str):
        """
        Create a new storage instance.

        Parameters
        ----------
        db_url : str
            SQLAlchemy database connection string.
        """
        super().__init__(db_url=db_url)
        self._initialized: bool = False

    @override
    def init(self) -> None:
        """
        Initialize the storage by creating database structures
        and preparing the shared SQLAlchemy session.

        Notes
        -----
        This method must be called before using any CRUD operations.
        """

        super().init()
        self._initialized = True

    def _get_session(self) -> SessionType:
        """
        Return the active SQLAlchemy session.

        Returns
        -------
        SessionType
            The initialized SQLAlchemy session.

        Raises
        ------
        RuntimeError
            If the storage has not been initialized via :meth:`init`.
        """
        if not getattr(self, "_initialized", False):
            raise RuntimeError("Storage not initialized. Call init() first.")
        return AlchemyTimeComplexityStorage.session

    @override
    def get_data(self, query: TimeComplexityQuery) -> TimeComplexityModel | None:
        """
        Retrieve time complexity data that matches a given query.

        Parameters
        ----------
        query : TimeComplexityQuery
            Query parameters containing criterion configuration,
            sample size, and Monte-Carlo count.

        Returns
        -------
        TimeComplexityModel or None
            The matching record, or ``None`` if no entry exists.
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

    @override
    def insert_data(self, data: TimeComplexityModel) -> None:
        """
        Insert a new time complexity record or update an existing one.

        If a record with the same unique key (criterion parameters,
        sample size, Monte-Carlo count) already exists, it is updated.
        Otherwise, a new record is created.

        Parameters
        ----------
        data : TimeComplexityModel
            The time complexity measurement to store.

        Notes
        -----
        - Existing records have their ``experiment_id`` and ``results_times`` replaced.
        - ``criterion_parameters`` and ``results_times`` are serialized to JSON.
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

    @override
    def delete_data(self, query: TimeComplexityQuery) -> None:
        """
        Delete time complexity data matching the given query.

        Parameters
        ----------
        query : TimeComplexityQuery
            The parameters identifying which record to delete.

        Notes
        -----
        The method silently does nothing if no matching record exists.
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
