from dataclasses import dataclass

from pysatl_experiment.configuration.experiment_config.critical_value.critical_value import (
    CriticalValueExperimentConfig,
)
from pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData


@dataclass
class CriticalValueExperimentData(ExperimentData[CriticalValueExperimentConfig]):
    """
    Critical value experiment data.
    """
