"""Critical value experiment data model."""

from dataclasses import dataclass

from src.pysatl_experiment.configuration.experiment_config.critical_value import CriticalValueExperimentConfig
from src.pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData


@dataclass
class CriticalValueExperimentData(ExperimentData[CriticalValueExperimentConfig]):
    """Experiment data for critical value estimation."""
