from __future__ import annotations

import json
from typing import ClassVar

from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import override

from pysatl_experiment.persistence.db_store.base import ModelBase, SessionType
from pysatl_experiment.persistence.db_store.model import AbstractDbStore
from pysatl_experiment.persistence.model.power.power import IPowerStorage, PowerModel, PowerQuery


class AlchemyPower(ModelBase):
    """
    SQLAlchemy ORM model representing precomputed statistical power results
    for a specific experiment, criterion, alternative hypothesis, and
    Monte-Carlo simulation setup.

    Each row contains a unique combination of:
        - criterion type and its parameters,
        - sample size,
        - alternative hypothesis and its parameters,
        - Monte-Carlo simulation count,
        - significance level.

    The uniqueness of these combinations is enforced by
    the ``uq_power_unique`` constraint.

    Attributes:
        id (int): Primary key of the record.
        experiment_id (int): Identifier of the experiment this power result
            belongs to.
        criterion_code (str): Code of the statistical criterion used
            (e.g., test type).
        criterion_parameters (str): JSON-encoded or serialized parameters
            of the criterion.
        sample_size (int): Sample size for which the power value was
            computed.
        alternative_code (str): Code of the alternative hypothesis used
            in the simulation.
        alternative_parameters (str): JSON-encoded or serialized parameters
            of the alternative hypothesis.
        monte_carlo_count (int): Number of Monte-Carlo simulations performed.
        significance_level (float): Significance level (alpha) used
            for the test.
        results_criteria (str): Serialized result of the power computation,
            typically containing power values or related statistics.
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
    SQLAlchemy-backed storage implementation for persisting and retrieving
    statistical power calculation results.

    This class manages CRUD operations for :class:`AlchemyPower` entities,
    providing a database-backed implementation of the ``IPowerStorage`` interface.
    It stores and queries power computation results based on combinations of
    criterion settings, sample size, alternative hypothesis parameters,
    Monte-Carlo configuration, and significance level.

    The storage must be explicitly initialized by calling :meth:`init` before any
    database operations can be performed.

    Attributes:
        session (SessionType): A SQLAlchemy session shared across all instances.
        _initialized (bool): Internal flag indicating whether the storage
            was properly initialized via :meth:`init`.
    """

    session: ClassVar[SessionType]

    def __init__(self, db_url: str):
        """
        Initialize the storage with a database connection URL.

        Args:
            db_url (str): SQLAlchemy database URL used to configure the connection.
        """
        super().__init__(db_url=db_url)
        self._initialized: bool = False

    @override
    def init(self) -> None:
        """
        Initialize the underlying database engine and session.

        Must be called before any read/write operations. Sets the internal
        ``_initialized`` flag to ensure :meth:`_get_session` returns
        a valid session instance.
        """
        super().init()
        self._initialized = True

    def _get_session(self) -> SessionType:
        """
        Return the active SQLAlchemy session.

        Raises:
            RuntimeError: If the storage has not been initialized via :meth:`init`.

        Returns:
            SessionType: The SQLAlchemy session used for database operations.
        """
        if not getattr(self, "_initialized", False):
            raise RuntimeError("Storage not initialized. Call init() first.")
        return AlchemyPowerStorage.session

    @override
    def get_data(self, query: PowerQuery) -> PowerModel | None:
        """
        Retrieve a power computation result matching the given query parameters.

        All parameter dictionaries are JSON-serialized for correct matching
        against stored database values.

        Args:
            query (PowerQuery): Query parameters defining the criterion, alternative,
                sample size, Monte-Carlo configuration, and significance level.

        Returns:
            PowerModel | None:
                - ``PowerModel`` with the stored results if a matching entry exists.
                - ``None`` if no record matches the query.
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

    @override
    def insert_data(self, data: PowerModel) -> None:
        """
        Insert a new power computation result or update an existing entry.

        If a record with the same unique parameter combination already exists,
        only the ``experiment_id`` and ``results_criteria`` fields are updated.
        Otherwise, a new ``AlchemyPower`` row is created.

        Args:
            data (PowerModel): The power computation result to store.
        """
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
                results_criteria=json.dumps(data.results_criteria),
            )
            self._get_session().add(entity)
        else:
            existing.experiment_id = int(data.experiment_id)
            existing.results_criteria = json.dumps(data.results_criteria)
        self._get_session().commit()

    @override
    def delete_data(self, query: PowerQuery) -> None:
        """
        Delete a stored power computation result matching the given parameters.

        Args:
            query (PowerQuery): Definition of the criterion, alternative,
                and simulation parameters identifying the record to delete.
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
