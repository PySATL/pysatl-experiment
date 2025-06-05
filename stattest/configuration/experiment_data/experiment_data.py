from dataclasses import dataclass
from typing import Generic, TypeVar

from stattest.configuration.experiment_config.experiment_config import ExperimentConfig


C = TypeVar("C", bound=ExperimentConfig)


@dataclass
class ExperimentData(Generic[C]):
    """
    Experiment data.
    """

    name: str
    config: C
