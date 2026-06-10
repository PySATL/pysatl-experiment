"""Parallel task specifications."""

from dataclasses import dataclass, field

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

    # For critical value & time complexity experiments
    hypothesis_generator: str = ""
    """Hypothesis generator name."""
    hypothesis_parameters: list[float] = field(default_factory=list)
    """Hypothesis generator parameters."""

    # For power experiments
    alternative_generator: str = ""
    """Alternative generator name."""
    alternative_parameters: list[float] = field(default_factory=list)
    """Alternative generator parameters."""
    significance_level: float | None = None
    """Significance level for power experiments."""
