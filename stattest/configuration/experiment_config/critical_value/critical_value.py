from dataclasses import dataclass

from stattest.configuration.experiment_config.experiment_config import ExperimentConfig


@dataclass
class CriticalValueExperimentConfig(ExperimentConfig):
    """
    Critical value experiment configuration.
    """
    significance_levels: list[float]
