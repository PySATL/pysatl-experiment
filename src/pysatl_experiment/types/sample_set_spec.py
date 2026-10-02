"""Description of a sample set, independent of storage and execution."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class SampleSetSpec:
    """Select an exact count from one experiment, sample series and sample size."""

    experiment_name: str
    generator_code: str
    sample_size: int
    samples_count: int

    def __post_init__(self) -> None:
        """Reject empty identifiers and invalid dimensions."""
        for name in ("experiment_name", "generator_code"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty string")
        for name in ("sample_size", "samples_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
