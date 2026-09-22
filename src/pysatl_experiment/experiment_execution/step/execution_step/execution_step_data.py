"""Data containers for experiment execution steps."""

from dataclasses import dataclass
from typing import Any

from pysatl_criterion.statistics import AbstractGoodnessOfFitStatistic

from pysatl_experiment.configuration.models.parameters import NumericParameters


@dataclass
class ExecutionStepData:
    """Data for execution step."""

    statistics: AbstractGoodnessOfFitStatistic
    sample_size: int
    criterion_parameters: NumericParameters


@dataclass
class HypothesisGeneratorData:
    """Data for hypothesis generator."""

    generator_name: str
    parameters: dict[str, Any] | list[float]

    @property
    def generator_code(self) -> str:
        """Return generator code using the newer naming convention."""
        return self.generator_name
