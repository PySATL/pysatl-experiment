"""Execution-facing sample loading contracts."""

from typing import Protocol

from pysatl_experiment.types import SampleBatch, SampleSetSpec


class SampleSource(Protocol):
    """Load the complete sample set requested by a computation."""

    def load(self, spec: SampleSetSpec) -> SampleBatch:
        """Return a validated batch for the requested sample set."""
        ...


class SampleSourceFactory(Protocol):
    """Serializable factory creating a source inside the execution process."""

    def __call__(self) -> SampleSource:
        """Create a source without transferring open database connections."""
        ...
