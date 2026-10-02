"""Data models and queries for random values."""

from dataclasses import dataclass

from pysatl_criterion.persistence.models.base import DataModel

from pysatl_experiment.persistence.models.bulk import BulkBatch
from pysatl_experiment.persistence.validation import require_nonempty_name, require_positive_integer


@dataclass
class RandomValuesModel(DataModel):
    """One sample in a configured series, with its actual numeric generator parameters.

    ``generator_code`` identifies the original fixed parameters and ranges shared
    by the series; ``generator_parameters`` records this sample's realization.
    """

    experiment_name: str
    generator_code: str
    generator_parameters: dict[str, float]
    sample_size: int
    data: list[float]

    def __post_init__(self) -> None:
        """Validate the experiment scope and sample dimensions."""
        require_nonempty_name(self.experiment_name, "experiment_name")
        require_nonempty_name(self.generator_code, "generator_code")
        require_positive_integer(self.sample_size, "sample_size")
        if len(self.data) != self.sample_size:
            raise ValueError("sample_size must equal the number of values in data")


@dataclass(frozen=True, kw_only=True)
class RandomValuesFilter:
    """Select samples of one experiment; None leaves an optional field unrestricted."""

    experiment_name: str
    generator_code: str | None = None
    sample_size: int | None = None

    def __post_init__(self) -> None:
        """Validate the experiment scope and sample dimensions."""
        require_nonempty_name(self.experiment_name, "experiment_name")
        if self.generator_code is not None:
            require_nonempty_name(self.generator_code, "generator_code")
        if self.sample_size is not None:
            require_positive_integer(self.sample_size, "sample_size")


RandomValuesBatch = BulkBatch[RandomValuesModel]
