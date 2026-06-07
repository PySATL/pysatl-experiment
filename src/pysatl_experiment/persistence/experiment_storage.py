"""
Experiment persistence layer (SQLAlchemy implementation).

This module provides a database-backed storage implementation for experiments.

Notes
-----
- Experiments are identified by a full configuration signature.
- JSON-serialized fields are used in equality comparisons.
- Serialization consistency is critical for correct query behavior.
- Execution state is tracked via boolean status flags.
"""

from typing import ClassVar

from sqlalchemy import JSON, Integer, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column

from src.pysatl_experiment.persistence.db_store import ModelBase, SessionType
from src.pysatl_experiment.persistence.db_store.model import AbstractDbStore
from src.pysatl_experiment.persistence.model.experiment import ExperimentModel, ExperimentQuery, IExperimentStorage


class AlchemyExperiment(ModelBase):
    """
    SQLAlchemy ORM model for experiment configuration storage.

    Each row represents a fully defined experiment configuration and its state.

    Attributes
    ----------
    id : int
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
    Uniqueness is enforced via a composite key over all configuration fields.

    Warning
    -------
    JSON serialization order affects uniqueness and lookup correctness.
    """

    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

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

    __table_args__ = (
        UniqueConstraint(
            "experiment_type",
            "storage_connection",
            "run_mode",
            "report_mode",
            "hypothesis",
            "generator_type",
            "executor_type",
            "report_builder_type",
            "sample_sizes",
            "monte_carlo_count",
            "criteria",
            "alternatives",
            "significance_levels",
            name="uix_limit_distribution",
        ),
    )


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
    This storage relies on strict equality matching for all fields,
    including JSON-encoded structures.
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
        """
        Insert or update experiment record.

        Parameters
        ----------
        model : ExperimentModel
            Experiment data to persist.

        Notes
        -----
        - If record exists, only execution state is updated.
        - Otherwise a new record is inserted.
        """
        with self.session() as session:
            stmt = select(AlchemyExperiment).where(
                AlchemyExperiment.experiment_type == model.experiment_type,
                AlchemyExperiment.storage_connection == model.storage_connection,
                AlchemyExperiment.run_mode == model.run_mode,
                AlchemyExperiment.report_mode == model.report_mode,
                AlchemyExperiment.hypothesis == model.hypothesis,
                AlchemyExperiment.generator_type == model.generator_type,
                AlchemyExperiment.executor_type == model.executor_type,
                AlchemyExperiment.report_builder_type == model.report_builder_type,
                AlchemyExperiment.sample_sizes == model.sample_sizes,
                AlchemyExperiment.monte_carlo_count == model.monte_carlo_count,
                AlchemyExperiment.criteria == model.criteria,
                AlchemyExperiment.alternatives == model.alternatives,
                AlchemyExperiment.significance_levels == model.significance_levels,
            )

            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.is_generation_done = bool(model.is_generation_done)
                existing.is_execution_done = bool(model.is_execution_done)
                existing.is_report_building_done = bool(model.is_report_building_done)
                existing.parallel_workers = model.parallel_workers
            else:
                session.add(self._to_orm(model))

            session.commit()

    def get_data(self, query: ExperimentQuery) -> ExperimentModel | None:
        """
        Retrieve experiment by full configuration match.

        Parameters
        ----------
        query : ExperimentQuery
            Query defining full experiment signature.

        Returns
        -------
        ExperimentModel or None
            Found experiment or None if not exists.

        Notes
        -----
        Matching is strict and includes JSON equality.
        """
        with self.session() as session:
            stmt = select(AlchemyExperiment).where(
                AlchemyExperiment.experiment_type == query.experiment_type,
                AlchemyExperiment.storage_connection == query.storage_connection,
                AlchemyExperiment.run_mode == query.run_mode,
                AlchemyExperiment.report_mode == query.report_mode,
                AlchemyExperiment.hypothesis == query.hypothesis,
                AlchemyExperiment.generator_type == query.generator_type,
                AlchemyExperiment.executor_type == query.executor_type,
                AlchemyExperiment.report_builder_type == query.report_builder_type,
                AlchemyExperiment.sample_sizes == query.sample_sizes,
                AlchemyExperiment.monte_carlo_count == query.monte_carlo_count,
                AlchemyExperiment.criteria == query.criteria,
                AlchemyExperiment.alternatives == query.alternatives,
                AlchemyExperiment.significance_levels == query.significance_levels,
            )

            result = session.execute(stmt).scalar_one_or_none()
            return self._to_model(result) if result else None

    def delete_data(self, query: ExperimentQuery) -> None:
        """
        Delete experiment by full configuration match.

        Parameters
        ----------
        query : ExperimentQuery
            Experiment identification query.
        """
        # TODO: implement soft delete
        with self.session() as session:
            stmt = select(AlchemyExperiment).where(
                AlchemyExperiment.experiment_type == query.experiment_type,
                AlchemyExperiment.storage_connection == query.storage_connection,
                AlchemyExperiment.run_mode == query.run_mode,
                AlchemyExperiment.report_mode == query.report_mode,
                AlchemyExperiment.hypothesis == query.hypothesis,
                AlchemyExperiment.sample_sizes == query.sample_sizes,
                AlchemyExperiment.monte_carlo_count == query.monte_carlo_count,
                AlchemyExperiment.criteria == query.criteria,
                AlchemyExperiment.alternatives == query.alternatives,
                AlchemyExperiment.significance_levels == query.significance_levels,
            )

            obj = session.execute(stmt).scalar_one_or_none()
            if obj:
                session.delete(obj)
                session.commit()

    def get_experiment_id(self, query: ExperimentQuery) -> int:
        """
        Retrieve experiment ID by configuration match.

        Parameters
        ----------
        query : ExperimentQuery
            Experiment signature.

        Returns
        -------
        int
            Experiment identifier.

        Raises
        ------
        ValueError
            If experiment is not found.
        """
        with self.session() as session:
            stmt = select(AlchemyExperiment.id).where(
                AlchemyExperiment.experiment_type == query.experiment_type,
                AlchemyExperiment.storage_connection == query.storage_connection,
                AlchemyExperiment.run_mode == query.run_mode,
                AlchemyExperiment.report_mode == query.report_mode,
                AlchemyExperiment.hypothesis == query.hypothesis,
                AlchemyExperiment.sample_sizes == query.sample_sizes,
                AlchemyExperiment.monte_carlo_count == query.monte_carlo_count,
                AlchemyExperiment.criteria == query.criteria,
                AlchemyExperiment.alternatives == query.alternatives,
                AlchemyExperiment.significance_levels == query.significance_levels,
            )

            result = session.execute(stmt).scalar_one_or_none()

            if result is None:
                raise ValueError("Experiment not found")

            return result

    def _update_status(self, experiment_id: int, field: str):
        """
        Update execution status field for experiment.

        Parameters
        ----------
        experiment_id : int
            Target experiment identifier.
        field : str
            Name of boolean status field.
        """
        with self.session() as session:
            obj = session.get(AlchemyExperiment, experiment_id)
            if not obj:
                raise ValueError("Experiment not found")

            setattr(obj, field, 1)
            session.commit()

    def set_generation_done(self, experiment_id: int):
        """
        Mark generation step as completed.

        Parameters
        ----------
        experiment_id : int
            Experiment identifier.
        """
        self._update_status(experiment_id, "is_generation_done")

    def set_execution_done(self, experiment_id: int):
        """
        Mark execution step as completed.

        Parameters
        ----------
        experiment_id : int
            Experiment identifier.
        """
        self._update_status(experiment_id, "is_execution_done")

    def set_report_building_done(self, experiment_id: int):
        """
        Mark report building step as completed.

        Parameters
        ----------
        experiment_id : int
            Experiment identifier.
        """
        self._update_status(experiment_id, "is_report_building_done")
