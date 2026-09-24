"""Configuration model for generation-only experiments."""

from dataclasses import dataclass
from typing import Any

from pysatl_criterion import DistributionType

from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.configuration.models.run_mode import RunMode


@dataclass(frozen=True)
class GenerationOnlyExperimentConfig:
    """Validated domain configuration for labelled sample generation."""

    experiment_type: ExperimentType
    storage_connection: str
    run_mode: RunMode
    distribution: DistributionType
    sample_sizes: list[int]
    samples_count: int
    parameter_config: dict[str, dict[str, Any]]
    seed: int
    parallel_workers: int = 1
