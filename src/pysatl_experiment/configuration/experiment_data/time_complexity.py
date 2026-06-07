"""Time complexity experiment data model."""

from dataclasses import dataclass

from src.pysatl_experiment.configuration.experiment_config.time_complexity import TimeComplexityExperimentConfig
from src.pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData


@dataclass
class TimeComplexityExperimentData(ExperimentData[TimeComplexityExperimentConfig]):
    """Experiment data for time complexity benchmarking."""
