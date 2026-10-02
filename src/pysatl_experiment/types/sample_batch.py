"""Prepared samples for a single computation."""

from dataclasses import dataclass

from .sample import Sample
from .sample_set_spec import SampleSetSpec


@dataclass(slots=True)
class SampleBatch:
    """Validate count and dimensions at construction without copying observations."""

    spec: SampleSetSpec
    samples: list[Sample]

    def __post_init__(self) -> None:
        """Require exactly the requested number of equally sized samples."""
        if len(self.samples) != self.spec.samples_count:
            raise ValueError("Sample count must equal spec.samples_count")
        for index, sample in enumerate(self.samples):
            if sample.size != self.spec.sample_size:
                raise ValueError(f"Sample {index} size must equal spec.sample_size")
