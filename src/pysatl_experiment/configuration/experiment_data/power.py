"""Power experiment data model."""

from dataclasses import dataclass

from src.pysatl_experiment.configuration.experiment_config.power import PowerExperimentConfig
from src.pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData


@dataclass
class PowerExperimentData(ExperimentData[PowerExperimentConfig]):
    """Experiment data for statistical power estimation."""
