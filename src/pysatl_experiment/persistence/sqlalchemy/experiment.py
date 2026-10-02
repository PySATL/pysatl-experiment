"""
Experiment persistence layer (SQLAlchemy implementation).

This module provides a database-backed storage implementation for experiments.

Notes
-----
- Experiments are identified by name.
- JSON-serialized fields are used in equality comparisons.
- Serialization consistency is critical for correct query behavior.
- Execution state is tracked via boolean status flags.
"""

from dataclasses import asdict
from typing import ClassVar

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from pysatl_experiment.persistence.contracts.experiment import IExperimentStorage
from pysatl_experiment.persistence.models.experiment import ExperimentModel, ExperimentQuery
from pysatl_experiment.persistence.sqlalchemy.base import AbstractDbStore, ModelBase, SessionType


class AlchemyExperiment(ModelBase):
    """
    SQLAlchemy ORM model for experiment configuration storage.

    Each row represents a fully defined experiment configuration and its state.

    Attributes
    ----------
    experiment_name : str
        Primary key of the experiment record.

    experiment_type : str
        Type of experiment (critical value, power, time complexity).

    storage_connection : str
        Identifier of storage backend connection.

    run_mode : str
        Execution mode (e.g., overwrite / append).

    report_mode : str
        Report generation mode.

    hypothesis : str
        Hypothesis type used in experiment.

    generator_type : str
        Random variable generator type.

    executor_type : str
        Execution engine type.

    report_builder_type : str
        Report generation backend type.

    sample_sizes : list[int]
        List of sample sizes used in experiment.

    monte_carlo_count : int
        Number of Monte-Carlo simulations.

    criteria : dict[str, list[float]]
        Statistical criteria and their parameters.

    alternatives : dict[str, list[float]]
        Alternative hypothesis configurations.

    significance_levels : list[float]
        Significance levels used in testing.

    parallel_workers : int
        Number of parallel workers used for execution.

    is_generation_done : bool
        Whether generation step is completed.

    is_execution_done : bool
        Whether execution step is completed.

    is_report_building_done : bool
        Whether report building step is completed.

    Notes
    -----
    The experiment name is the unique identity of a record.
    """

    __tablename__ = "experiments"

    experiment_name: Mapped[str] = mapped_column(String, primary_key=True)

    experiment_type: Mapped[str] = mapped_column(String, nullable=False)
    storage_connection: Mapped[str] = mapped_column(String, nullable=False)
    run_mode: Mapped[str] = mapped_column(String, nullable=False)
    report_mode: Mapped[str] = mapped_column(String, nullable=False)
    hypothesis: Mapped[str] = mapped_column(String, nullable=False)

    generator_type: Mapped[str] = mapped_column(String, nullable=False)
    executor_type: Mapped[str] = mapped_column(String, nullable=False)
    report_builder_type: Mapped[str] = mapped_column(String, nullable=False)

    sample_sizes: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    monte_carlo_count: Mapped[int] = mapped_column(Integer, nullable=False)

    criteria: Mapped[dict[str, list[float]]] = mapped_column(JSON, nullable=False)
    alternatives: Mapped[dict[str, list[float]]] = mapped_column(JSON, nullable=False)
    significance_levels: Mapped[list[float]] = mapped_column(JSON, nullable=False)

    parallel_workers: Mapped[int] = mapped_column(Integer, nullable=False)

    is_generation_done: Mapped[bool] = mapped_column(Integer, default=0)
    is_execution_done: Mapped[bool] = mapped_column(Integer, default=0)
    is_report_building_done: Mapped[bool] = mapped_column(Integer, default=0)


class AlchemyExperimentStorage(AbstractDbStore, IExperimentStorage):
    """
    SQLAlchemy-backed experiment storage implementation.

    Provides persistence and retrieval of experiment configurations and state.

    Attributes
    ----------
    session : ClassVar[SessionType]
        Shared SQLAlchemy session factory used for DB operations.

    _initialized : bool
        Indicates whether storage has been initialized via `init()`.

    Notes
    -----
    Configuration fields do not participate in experiment identity.
    """

    session: ClassVar[SessionType]

    def __init__(self, db_url: str) -> None:
        """
        Initialize experiment storage.

        Parameters
        ----------
        db_url : str
            SQLAlchemy database connection string.

        Notes
        -----
        The storage is not usable until `init()` is called.
        """
        super().__init__(db_url=db_url)
        self._initialized: bool = False

    def init(self) -> None:
        """
        Initialize database engine and session.

        Notes
        -----
        Must be called before any database operations.
        """
        super().init()
        self._initialized = True

    @staticmethod
    def _to_orm(model: ExperimentModel) -> AlchemyExperiment:
        """
        Convert domain model to ORM entity.

        Parameters
        ----------
        model : ExperimentModel
            Domain experiment model.

        Returns
        -------
        AlchemyExperiment
            ORM representation of the experiment.
        """
        return AlchemyExperiment(
            experiment_name=model.experiment_name,
            experiment_type=model.experiment_type,
            storage_connection=model.storage_connection,
            run_mode=model.run_mode,
            report_mode=model.report_mode,
            hypothesis=model.hypothesis,
            generator_type=model.generator_type,
            executor_type=model.executor_type,
            report_builder_type=model.report_builder_type,
            sample_sizes=model.sample_sizes,
            monte_carlo_count=model.monte_carlo_count,
            criteria=model.criteria,
            alternatives=model.alternatives,
            significance_levels=model.significance_levels,
            parallel_workers=model.parallel_workers,
            is_generation_done=int(model.is_generation_done),
            is_execution_done=int(model.is_execution_done),
            is_report_building_done=int(model.is_report_building_done),
        )

    @staticmethod
    def _to_model(orm: AlchemyExperiment) -> ExperimentModel:
        """
        Convert ORM entity to domain model.

        Parameters
        ----------
        orm : AlchemyExperiment
            ORM database entity.

        Returns
        -------
        ExperimentModel
            Domain representation of the experiment.
        """
        return ExperimentModel(
            experiment_name=orm.experiment_name,
            experiment_type=orm.experiment_type,
            storage_connection=orm.storage_connection,
            run_mode=orm.run_mode,
            report_mode=orm.report_mode,
            hypothesis=orm.hypothesis,
            generator_type=orm.generator_type,
            executor_type=orm.executor_type,
            report_builder_type=orm.report_builder_type,
            sample_sizes=orm.sample_sizes,
            monte_carlo_count=orm.monte_carlo_count,
            criteria=orm.criteria,
            alternatives=orm.alternatives,
            significance_levels=orm.significance_levels,
            parallel_workers=orm.parallel_workers,
            is_generation_done=bool(orm.is_generation_done),
            is_execution_done=bool(orm.is_execution_done),
            is_report_building_done=bool(orm.is_report_building_done),
        )

    def insert_data(self, model: ExperimentModel) -> None:
        """Insert or replace configuration and progress for the named experiment."""
        with self.session() as session:
            existing = session.get(AlchemyExperiment, model.experiment_name)
            if existing is None:
                session.add(self._to_orm(model))
            else:
                for name, value in asdict(model).items():
                    setattr(existing, name, value)
            session.commit()

    def get_data(self, query: ExperimentQuery) -> ExperimentModel | None:
        """Retrieve configuration and progress by experiment name."""
        with self.session() as session:
            result = session.get(AlchemyExperiment, query.experiment_name)
            return self._to_model(result) if result is not None else None

    def delete_data(self, query: ExperimentQuery) -> None:
        """Delete only the named experiment record."""
        with self.session() as session:
            result = session.get(AlchemyExperiment, query.experiment_name)
            if result is not None:
                session.delete(result)
                session.commit()

    def _update_status(self, experiment_name: str, field: str) -> None:
        with self.session() as session:
            result = session.get(AlchemyExperiment, experiment_name)
            if result is None:
                raise ValueError(f"Experiment {experiment_name!r} not found")
            setattr(result, field, True)
            session.commit()

    def set_generation_done(self, experiment_name: str) -> None:
        """Mark generation completed for the named experiment."""
        self._update_status(experiment_name, "is_generation_done")

    def set_execution_done(self, experiment_name: str) -> None:
        """Mark execution completed for the named experiment."""
        self._update_status(experiment_name, "is_execution_done")

    def set_report_building_done(self, experiment_name: str) -> None:
        """Mark reporting completed for the named experiment."""
        self._update_status(experiment_name, "is_report_building_done")
