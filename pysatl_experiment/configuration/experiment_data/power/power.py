from dataclasses import dataclass

from pysatl_experiment.configuration.experiment_config.power.power import PowerExperimentConfig
from pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData


@dataclass
class PowerExperimentData(ExperimentData[PowerExperimentConfig]):
    """
    Power experiment data.
    """
