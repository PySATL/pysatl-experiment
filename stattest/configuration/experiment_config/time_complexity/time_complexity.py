from dataclasses import dataclass

from stattest.configuration.experiment_config.experiment_config import ExperimentConfig


@dataclass
class TimeComplexityExperimentConfig(ExperimentConfig):
    """
    Time complexity experiment configuration.
    """
