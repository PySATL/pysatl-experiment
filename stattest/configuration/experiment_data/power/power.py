from dataclasses import dataclass

from stattest.configuration.experiment_config.power.power import PowerExperimentConfig
from stattest.configuration.experiment_data.experiment_data import ExperimentData


@dataclass
class PowerExperimentData(ExperimentData[PowerExperimentConfig]):
    """
    Power experiment data.
    """
