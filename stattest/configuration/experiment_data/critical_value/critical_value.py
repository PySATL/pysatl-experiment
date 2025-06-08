from dataclasses import dataclass

from stattest.configuration.experiment_config.critical_value.critical_value import (
    CriticalValueExperimentConfig,
)
from stattest.configuration.experiment_data.experiment_data import ExperimentData


@dataclass
class CriticalValueExperimentData(ExperimentData[CriticalValueExperimentConfig]):
    """
    Critical value experiment data.
    """
