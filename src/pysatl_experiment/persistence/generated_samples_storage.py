"""SQLAlchemy storage for generation-only runs and samples."""

from pysatl_criterion.persistence.sqlalchemy.alchemy_decorator import CompressedFloatArray
from sqlalchemy import JSON, BigInteger, Boolean, ForeignKey, Integer, String, UniqueConstraint, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column

from pysatl_experiment.persistence.db_store.base import ModelBase
from pysatl_experiment.persistence.db_store.model import AbstractDbStore
from pysatl_experiment.persistence.models.generated_samples import GeneratedSampleModel, GenerationRunModel


class AlchemyGenerationRun(ModelBase):
    """Persisted configuration of a generation-only run."""

    __tablename__ = "generation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    distribution: Mapped[str] = mapped_column(String, nullable=False, index=True)
    sample_sizes: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    samples_count: Mapped[int] = mapped_column(Integer, nullable=False)
    parameter_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    config_fingerprint: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class AlchemyGeneratedSample(ModelBase):
    """Persisted generated sample with realized parameters."""

    __tablename__ = "generated_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    generation_run_id: Mapped[int] = mapped_column(
        ForeignKey("generation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    sample_num: Mapped[int] = mapped_column(Integer, nullable=False)
    parameters: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    sample_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    data: Mapped[list[float]] = mapped_column(CompressedFloatArray(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "generation_run_id",
            "sample_size",
            "sample_num",
            name="uq_generated_samples_run_size_number",
        ),
    )


class GeneratedSamplesStorage(AbstractDbStore):
    """Store and retrieve generation-only runs and individual samples."""

    def create_run(self, model: GenerationRunModel) -> int:
        """Create a run or return the id of the same configuration."""
        with self.session() as session:
            existing_id = session.scalar(
                select(AlchemyGenerationRun.id).where(
                    AlchemyGenerationRun.config_fingerprint == model.config_fingerprint
                )
            )
            if existing_id is not None:
                return existing_id

            entity = AlchemyGenerationRun(
                name=model.name,
                distribution=model.distribution,
                sample_sizes=model.sample_sizes,
                samples_count=model.samples_count,
                parameter_config=model.parameter_config,
                seed=model.seed,
                config_fingerprint=model.config_fingerprint,
                is_complete=model.is_complete,
            )
            session.add(entity)
            session.commit()
            return entity.id

    def get_run(self, run_id: int) -> GenerationRunModel | None:
        """Return a generation run by primary key."""
        with self.session() as session:
            entity = session.get(AlchemyGenerationRun, run_id)
            if entity is None:
                return None
            return self._to_run_model(entity)

    def get_run_by_fingerprint(self, fingerprint: str) -> GenerationRunModel | None:
        """Return a generation run by its canonical configuration fingerprint."""
        with self.session() as session:
            entity = session.scalar(
                select(AlchemyGenerationRun).where(AlchemyGenerationRun.config_fingerprint == fingerprint)
            )
            return self._to_run_model(entity) if entity is not None else None

    def delete_run(self, run_id: int) -> None:
        """Delete one resolved generation run and only its generated samples."""
        with self.session() as session:
            session.execute(delete(AlchemyGeneratedSample).where(AlchemyGeneratedSample.generation_run_id == run_id))
            session.execute(delete(AlchemyGenerationRun).where(AlchemyGenerationRun.id == run_id))
            session.commit()

    def insert_sample(self, model: GeneratedSampleModel) -> None:
        """Insert one sample without replacing an existing sample number."""
        self.insert_samples([model])

    def insert_samples(self, models: list[GeneratedSampleModel]) -> None:
        """Insert a batch of samples in one transaction."""
        if not models:
            return
        with self.session() as session:
            session.add_all(
                [
                    AlchemyGeneratedSample(
                        generation_run_id=model.generation_run_id,
                        sample_size=model.sample_size,
                        sample_num=model.sample_num,
                        parameters=model.parameters,
                        sample_seed=model.sample_seed,
                        data=model.data,
                    )
                    for model in models
                ]
            )
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                raise

    def get_sample(self, run_id: int, sample_size: int, sample_num: int) -> GeneratedSampleModel | None:
        """Return one sample identified within a generation run."""
        with self.session() as session:
            entity = session.scalar(
                select(AlchemyGeneratedSample).where(
                    AlchemyGeneratedSample.generation_run_id == run_id,
                    AlchemyGeneratedSample.sample_size == sample_size,
                    AlchemyGeneratedSample.sample_num == sample_num,
                )
            )
            if entity is None:
                return None
            return GeneratedSampleModel(
                id=entity.id,
                generation_run_id=entity.generation_run_id,
                sample_size=entity.sample_size,
                sample_num=entity.sample_num,
                parameters=entity.parameters,
                sample_seed=entity.sample_seed,
                data=entity.data,
            )

    def get_existing_sample_numbers(self, run_id: int, sample_size: int) -> set[int]:
        """Return sample numbers already persisted for one run and size."""
        with self.session() as session:
            numbers = session.scalars(
                select(AlchemyGeneratedSample.sample_num).where(
                    AlchemyGeneratedSample.generation_run_id == run_id,
                    AlchemyGeneratedSample.sample_size == sample_size,
                )
            )
            return set(numbers)

    def mark_run_complete(self, run_id: int) -> None:
        """Mark an existing generation run as complete."""
        with self.session() as session:
            entity = session.get(AlchemyGenerationRun, run_id)
            if entity is None:
                raise ValueError(f"Generation run {run_id} does not exist")
            entity.is_complete = True
            session.commit()

    @staticmethod
    def _to_run_model(entity: AlchemyGenerationRun) -> GenerationRunModel:
        return GenerationRunModel(
            id=entity.id,
            name=entity.name,
            distribution=entity.distribution,
            sample_sizes=entity.sample_sizes,
            samples_count=entity.samples_count,
            parameter_config=entity.parameter_config,
            seed=entity.seed,
            config_fingerprint=entity.config_fingerprint,
            is_complete=entity.is_complete,
        )
