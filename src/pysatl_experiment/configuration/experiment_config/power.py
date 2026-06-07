"""Power experiment configuration model."""

from dataclasses import dataclass

from pysatl_experiment.configuration.experiment_config.experiment_config import ExperimentConfig
from pysatl_experiment.configuration.model.alternative import Alternative


@dataclass
class PowerExperimentConfig(ExperimentConfig):
    """
    Statistical power experiment configuration.

    Attributes
    ----------
    alternatives : list[Alternative]
        Alternative distributions used for power estimation.
    significance_levels : list[float]
        Significance levels used during testing.
    """

    alternatives: list[Alternative]
    significance_levels: list[float]
