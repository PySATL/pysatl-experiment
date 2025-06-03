from dataclasses import dataclass

from stattest.configuration.experiment_config.experiment_config import ExperimentConfig
from stattest.configuration.model.alternative.alternative import Alternative


@dataclass
class PowerExperimentConfig(ExperimentConfig):
    """
    Power experiment configuration.
    """

    alternatives: list[Alternative]
    significance_levels: list[float]
