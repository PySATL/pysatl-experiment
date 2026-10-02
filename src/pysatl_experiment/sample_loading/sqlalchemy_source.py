"""Construct SQLAlchemy sample sources within the executing process."""

from dataclasses import dataclass

from pysatl_experiment.persistence.contracts.random_values import IRandomValuesStorage
from pysatl_experiment.persistence.sqlalchemy.random_values import AlchemyRandomValuesStorage
from pysatl_experiment.types import SampleBatch, SampleSetSpec

from .loading import load_sample_batch
from .source import SampleSource, SampleSourceFactory


@dataclass
class StorageSampleSource(SampleSource):
    """Read batches through an initialized random-values storage."""

    storage: IRandomValuesStorage

    def load(self, spec: SampleSetSpec) -> SampleBatch:
        """Load matching samples and validate their count and dimensions."""
        return load_sample_batch(self.storage, spec)


@dataclass(frozen=True, slots=True)
class SqlAlchemySampleSourceFactory(SampleSourceFactory):
    """Pass only the connection URL across process boundaries."""

    connection: str

    def __call__(self) -> StorageSampleSource:
        """Initialize storage locally before constructing a sample source."""
        storage = AlchemyRandomValuesStorage(self.connection)
        storage.init()
        return StorageSampleSource(storage)
