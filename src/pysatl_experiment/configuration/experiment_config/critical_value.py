"""Critical value experiment configuration model."""

from dataclasses import dataclass

from pysatl_experiment.configuration.experiment_config.experiment_config import ExperimentConfig


@dataclass
class CriticalValueExperimentConfig(ExperimentConfig):
    """
    Critical value experiment configuration.

    Attributes
    ----------
    significance_levels : list[float]
        Significance levels used for critical value estimation.
    """

    significance_levels: list[float]
