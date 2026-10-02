"""Resolved criterion implementation and its construction parameters."""

from dataclasses import dataclass

from pysatl_criterion.statistics import AbstractGoodnessOfFitStatistic


@dataclass(frozen=True, slots=True)
class CriterionSpec:
    """Describe a statistic without constructing an instance in the parent process.

    The implementation must be a class defined in an importable module.
    Parameters include both hypothesis and criterion-specific settings.
    """

    code: str
    implementation: type[AbstractGoodnessOfFitStatistic]
    parameters: dict[str, float]

    def __post_init__(self) -> None:
        """Keep an independent snapshot of constructor arguments."""
        object.__setattr__(self, "parameters", dict(self.parameters))
