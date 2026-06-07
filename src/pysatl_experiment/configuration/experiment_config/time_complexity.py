"""Time complexity experiment configuration model."""

from dataclasses import dataclass

from src.pysatl_experiment.configuration.experiment_config.experiment_config import ExperimentConfig


@dataclass
class TimeComplexityExperimentConfig(ExperimentConfig):
    """Time complexity experiment configuration."""
