"""Shared, fully populated experiment step configurations."""

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from pysatl_experiment.types import ReportMode, StepType


@dataclass(frozen=True, kw_only=True)
class RequiredConfig:
    """Reject None fields at construction, including inside collections."""

    def __post_init__(self) -> None:
        """Check every dataclass field after initialization."""
        for item in fields(self):
            self._require_value(getattr(self, item.name), item.name)

    @classmethod
    def _require_value(cls, value: Any, path: str) -> None:
        if value is None:
            raise ValueError(f"{path} must not be None")
        if isinstance(value, dict):
            for key, child in value.items():
                cls._require_value(child, f"{path}[{key!r}]")
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                cls._require_value(child, f"{path}[{index}]")


@dataclass(frozen=True, kw_only=True)
class DistributionConfig(RequiredConfig):
    """Distribution identifier and its named numeric parameters."""

    distribution_type: str
    distribution_params: dict[str, float | list[float]]


@dataclass(frozen=True, kw_only=True)
class CriterionConfig(RequiredConfig):
    """Criterion identifier and its named numeric parameters."""

    criterion_code: str
    parameters: dict[str, float]


@dataclass(frozen=True, kw_only=True)
class GenerationConfig(RequiredConfig):
    """Generation settings common to all current experiments."""

    generator_type: StepType
    parallel_workers: int
    distributions: list[DistributionConfig]


@dataclass(frozen=True, kw_only=True)
class SampleGenerationConfig(GenerationConfig):
    """Generation settings for experiments consuming stored samples."""

    samples_count: int
    sample_sizes: list[int]


@dataclass(frozen=True, kw_only=True)
class ExecutionConfig(RequiredConfig):
    """Execution settings shared by the three current experiment kinds."""

    hypothesis: str
    hypothesis_params: dict[str, Any]
    criteria: list[CriterionConfig]
    executor_type: StepType
    monte_carlo_count: int
    parallel_workers: int
    significance_levels: list[float]
    write_batch_size: int = 20


@dataclass(frozen=True, kw_only=True)
class PowerExecutionConfig(ExecutionConfig):
    """Power execution additionally selects the sample sizes."""

    sample_sizes: list[int]


@dataclass(frozen=True, kw_only=True)
class ReportConfig(RequiredConfig):
    """Report settings shared by the current experiment kinds."""

    report_builder_type: StepType
    report_mode: ReportMode
    results_path: Path
