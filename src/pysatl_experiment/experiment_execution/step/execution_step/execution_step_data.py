"""Data containers for experiment execution steps."""

from dataclasses import dataclass

from pysatl_criterion.statistics import AbstractGoodnessOfFitStatistic


@dataclass
class ExecutionStepData:
    """Data for execution step."""

    statistics: AbstractGoodnessOfFitStatistic
    sample_size: int


@dataclass
class HypothesisGeneratorData:
    """Data for hypothesis generator."""

    generator_name: str
    parameters: list[float]
