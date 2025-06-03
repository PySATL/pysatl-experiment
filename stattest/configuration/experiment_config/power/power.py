from dataclasses import dataclass

from stattest.configuration.model.alternative.alternative import Alternative
from stattest.configuration.experiment_config.experiment_config import ExperimentConfig


@dataclass
class PowerExperimentConfig(ExperimentConfig):
    """
    Power experiment configuration.
    """
    alternatives: list[Alternative]
    significance_levels: list[float]
