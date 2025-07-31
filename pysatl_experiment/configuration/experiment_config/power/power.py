from dataclasses import dataclass

from pysatl_experiment.configuration.experiment_config.experiment_config import ExperimentConfig
from pysatl_experiment.configuration.model.alternative.alternative import Alternative


@dataclass
class PowerExperimentConfig(ExperimentConfig):
    """
    Power experiment configuration.
    """

    alternatives: list[Alternative]
    significance_levels: list[float]
