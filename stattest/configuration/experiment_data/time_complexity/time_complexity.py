from dataclasses import dataclass

from stattest.configuration.experiment_config.time_complexity.time_complexity import TimeComplexityExperimentConfig
from stattest.configuration.experiment_data.experiment_data import ExperimentData


@dataclass
class TimeComplexityExperimentData(ExperimentData[TimeComplexityExperimentConfig]):
    """
    Time complexity experiment data.
    """
