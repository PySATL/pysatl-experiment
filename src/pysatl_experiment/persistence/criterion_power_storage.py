"""
Power experiment persistence layer (SQLAlchemy implementation).

This module provides database models and storage implementation for
storing and retrieving precomputed statistical power results.

The module ensures uniqueness of these combinations via a database
constraint and provides CRUD operations over these results.
"""

from __future__ import annotations

import json
from typing import ClassVar

from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from pysatl_experiment.persistence.db_store.base import ModelBase, SessionType
from pysatl_experiment.persistence.db_store.model import AbstractDbStore
from pysatl_experiment.persistence.models.power import IPowerStorage, PowerModel, PowerQuery


class AlchemyPower(ModelBase):
    """
    SQLAlchemy ORM model representing precomputed statistical power results.

    Each row contains a unique combination of:
        - criterion type and its parameters,
        - sample size,
        - alternative hypothesis and its parameters,
        - Monte-Carlo simulation count,
        - significance level.

    The uniqueness of these combinations is enforced by
    the ``uq_power_unique`` constraint.

    Attributes
    ----------
    id : int
        Primary key of the record.
    experiment_id : int
        Identifier of the experiment this result belongs to.
    criterion_code : str
        Identifier of the statistical test / criterion.
    criterion_parameters : str
        JSON-encoded parameters of the criterion.
    sample_size : int
        Sample size used in simulation.
    alternative_code : str
        Identifier of the alternative hypothesis.
    alternative_parameters : str
        JSON-encoded parameters of the alternative hypothesis.
    monte_carlo_count : int
        Number of Monte-Carlo simulations performed.
    significance_level : float
        Significance level (alpha).
    results_criteria : str
        Serialized computation result (typically boolean array or power values).

    Notes
    -----
    This model stores serialized JSON fields as strings, which may require
    consistent serialization strategy across the system.
    """

    __tablename__ = "power"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
    experiment_id: Mapped[int] = mapped_column(Integer, nullable=False)  # type: ignore
    criterion_code: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    criterion_parameters: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # type: ignore
    alternative_code: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    alternative_parameters: Mapped[str] = mapped_column(String, nullable=False, index=True)  # type: ignore
    monte_carlo_count: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # type: ignore
    significance_level: Mapped[float] = mapped_column(Float, nullable=False, index=True)  # type: ignore
    results_criteria: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "criterion_code",
            "criterion_parameters",
            "sample_size",
            "alternative_code",
            "alternative_parameters",
            "monte_carlo_count",
            "significance_level",
            name="uq_power_unique",
        ),
    )


class AlchemyPowerStorage(AbstractDbStore, IPowerStorage):
    """
    SQLAlchemy-backed storage implementation for persisting and retrieving statistical power calculation results.

    This class manages CRUD operations for :class:`AlchemyPower` entities,
    providing a database-backed implementation of the ``IPowerStorage`` interface.
    It stores and queries power computation results based on combinations of
    criterion settings, sample size, alternative hypothesis parameters,
    Monte-Carlo configuration, and significance level.

    The storage must be explicitly initialized by calling :meth:`init` before any
    database operations can be performed.

    Attributes
    ----------
    session : SessionType:
        A SQLAlchemy session shared across all instances.
    _initialized : bool:
        Internal flag indicating whether the storage
        was properly initialized via :meth:`init`.
    """

    session: ClassVar[SessionType]

    def __init__(self, db_url: str):
        """
        Initialize storage with database connection URL.

        Parameters
        ----------
        db_url : str
            SQLAlchemy database connection string.

        Notes
        -----
        This constructor does not establish a database connection immediately.
        Call :meth:`init` to initialize the session.
        """
        super().__init__(db_url=db_url)
        self._initialized: bool = False

    def init(self) -> None:
        """
        Initialize database engine and SQLAlchemy session.

        This method must be called before performing any database operations.

        Side Effects
        ------------
        - Initializes SQLAlchemy engine
        - Creates session factory
        - Sets internal initialization flag

        Raises
        ------
        RuntimeError
            If initialization fails at the base storage layer.
        """
        super().init()
        self._initialized = True

    def _get_session(self) -> SessionType:
        """
        Retrieve active SQLAlchemy session.

        Returns
        -------
        SessionType
            Active database session bound to this storage.

        Raises
        ------
        RuntimeError
            If storage has not been initialized via :meth:`init`.

        Notes
        -----
        Session is shared at class level (ClassVar), meaning it is global
        across instances.
        """
        if not getattr(self, "_initialized", False):
            raise RuntimeError("Storage not initialized. Call init() first.")
        return AlchemyPowerStorage.session

    def get_data(self, query: PowerQuery) -> PowerModel | None:
        """
        Retrieve stored power result matching query parameters.

        Parameters
        ----------
        query : PowerQuery
            Query object defining:
                - criterion and parameters
                - sample size
                - alternative hypothesis
                - Monte-Carlo configuration
                - significance level

        Returns
        -------
        PowerModel | None
            Matching stored result or None if not found.

        Notes
        -----
        Matching is performed using JSON-serialized parameter comparison.

        This makes exact match required; semantically equivalent but differently
        serialized inputs will not match.
        """
        params_json = json.dumps(query.criterion_parameters)
        alt_params_json = json.dumps(query.alternative_parameters)
        row: AlchemyPower | None = (
            self._get_session()
            .query(AlchemyPower)
            .filter(
                AlchemyPower.criterion_code == query.criterion_code,
                AlchemyPower.criterion_parameters == params_json,
                AlchemyPower.sample_size == int(query.sample_size),
                AlchemyPower.alternative_code == query.alternative_code,
                AlchemyPower.alternative_parameters == alt_params_json,
                AlchemyPower.monte_carlo_count == int(query.monte_carlo_count),
                AlchemyPower.significance_level == float(query.significance_level),
            )
            .one_or_none()
        )
        if row is None:
            return None
        return PowerModel(
            experiment_id=int(row.experiment_id),
            criterion_code=query.criterion_code,
            criterion_parameters=query.criterion_parameters,
            sample_size=query.sample_size,
            alternative_code=query.alternative_code,
            alternative_parameters=query.alternative_parameters,
            monte_carlo_count=query.monte_carlo_count,
            significance_level=query.significance_level,
            results_criteria=json.loads(row.results_criteria),
        )

    def insert_data(self, data: PowerModel) -> None:
        """
        Insert or update a power computation result.

        If a matching record exists, only mutable fields are updated.
        Otherwise, a new record is created.

        Parameters
        ----------
        data : PowerModel
            Computed power result to store.

        Notes
        -----
        This method performs an UPSERT-like behavior implemented manually
        via SELECT + INSERT/UPDATE.
        """
        # TODO: change to UPSERT (ON CONFLICT DO UPDATE)?
        params_json = json.dumps(data.criterion_parameters)
        alt_params_json = json.dumps(data.alternative_parameters)
        existing: AlchemyPower | None = (
            self._get_session()
            .query(AlchemyPower)
            .filter(
                AlchemyPower.criterion_code == data.criterion_code,
                AlchemyPower.criterion_parameters == params_json,
                AlchemyPower.sample_size == int(data.sample_size),
                AlchemyPower.alternative_code == data.alternative_code,
                AlchemyPower.alternative_parameters == alt_params_json,
                AlchemyPower.monte_carlo_count == int(data.monte_carlo_count),
                AlchemyPower.significance_level == float(data.significance_level),
            )
            .one_or_none()
        )
        if existing is None:
            entity = AlchemyPower(
                experiment_id=int(data.experiment_id),
                criterion_code=data.criterion_code,
                criterion_parameters=params_json,
                sample_size=int(data.sample_size),
                alternative_code=data.alternative_code,
                alternative_parameters=alt_params_json,
                monte_carlo_count=int(data.monte_carlo_count),
                significance_level=float(data.significance_level),
                results_criteria=json.dumps([bool(x) for x in data.results_criteria]),
            )
            self._get_session().add(entity)
        else:
            existing.experiment_id = int(data.experiment_id)
            existing.results_criteria = json.dumps([bool(x) for x in data.results_criteria])
        self._get_session().commit()

    def delete_data(self, query: PowerQuery) -> None:
        """
        Delete stored power result matching query parameters.

        Parameters
        ----------
        query : PowerQuery
            Query defining record identity to delete.

        Notes
        -----
        Deletion is strict and requires exact parameter match.
        """
        params_json = json.dumps(query.criterion_parameters)
        alt_params_json = json.dumps(query.alternative_parameters)
        (
            self._get_session()
            .query(AlchemyPower)
            .filter(
                AlchemyPower.criterion_code == query.criterion_code,
                AlchemyPower.criterion_parameters == params_json,
                AlchemyPower.sample_size == int(query.sample_size),
                AlchemyPower.alternative_code == query.alternative_code,
                AlchemyPower.alternative_parameters == alt_params_json,
                AlchemyPower.monte_carlo_count == int(query.monte_carlo_count),
                AlchemyPower.significance_level == float(query.significance_level),
            )
            .delete()
        )
        self._get_session().commit()


# TODO: add sort_keys= TRUE??
