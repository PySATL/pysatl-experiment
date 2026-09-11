"""Parallel task specifications."""

from dataclasses import dataclass, field
from typing import Any

from pysatl_experiment.configuration.models.experiment_type import ExperimentType


@dataclass
class TaskSpec:
    """
    Universal pickle-serializable task specification.

    Contains only primitive serializable types.
    """

    experiment_type: ExperimentType
    """Experiment type."""
    statistic_class_name: str
    """Statistic class name."""
    statistic_module: str
    """Module containing statistic implementation."""
    sample_size: int
    """Generated sample size."""
    monte_carlo_count: int
    """Monte Carlo iterations count."""
    db_path: str
    """Database connection path."""
    experiment_name: str = ""
    """Experiment name used to scope generated samples."""
    criterion_code: str = ""
    """Criterion code used by result storage."""
    criterion_parameters: dict[str, float] | list[float] = field(default_factory=dict)
    """Criterion parameters used by result storage."""
    sample_generator_code: str = ""
    """Generator code used to load random samples."""
    sample_generator_parameters: dict[str, Any] | list[float] = field(default_factory=dict)
    """Generator parameters used to load random samples."""

    # For critical value & time complexity experiments
    hypothesis_generator: str = ""
    """Hypothesis generator name."""
    hypothesis_parameters: dict[str, Any] | list[float] = field(default_factory=list)
    """Hypothesis generator parameters."""

    # For power experiments
    alternative_generator: str = ""
    """Alternative generator name."""
    alternative_parameters: dict[str, Any] | list[float] = field(default_factory=list)
    """Alternative generator parameters."""
    significance_level: float | None = None
    """Significance level for power experiments."""
