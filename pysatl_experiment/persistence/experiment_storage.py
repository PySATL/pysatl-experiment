from typing import ClassVar

from sqlalchemy import JSON, Integer, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column

from pysatl_experiment.persistence.db_store import ModelBase, SessionType
from pysatl_experiment.persistence.db_store.model import AbstractDbStore
from pysatl_experiment.persistence.model.experiment.experiment import (
    ExperimentModel,
    ExperimentQuery,
    IExperimentStorage,
)


class AlchemyExperiment(ModelBase):
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
    session: ClassVar[SessionType]

    def __init__(self, db_url: str):
        super().__init__(db_url=db_url)
        self._initialized: bool = False

    def init(self):
        super().init()
        self._initialized = True

    def _to_orm(self, model: ExperimentModel) -> AlchemyExperiment:
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

    def _to_model(self, orm: AlchemyExperiment) -> ExperimentModel:
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
        with self.session() as session:
            obj = session.get(AlchemyExperiment, experiment_id)
            if not obj:
                raise ValueError("Experiment not found")

            setattr(obj, field, 1)
            session.commit()

    def set_generation_done(self, experiment_id: int):
        self._update_status(experiment_id, "is_generation_done")

    def set_execution_done(self, experiment_id: int):
        self._update_status(experiment_id, "is_execution_done")

    def set_report_building_done(self, experiment_id: int):
        self._update_status(experiment_id, "is_report_building_done")
