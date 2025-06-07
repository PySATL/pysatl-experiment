from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

from stattest.configuration.experiment_config.experiment_config import ExperimentConfig
from stattest.configuration.experiment_data.common.steps_done.steps_done import StepsDone


C = TypeVar("C", bound=ExperimentConfig)


@dataclass
class ExperimentData(Generic[C]):
    """
    Experiment data.
    """

    name: str
    config: C
    steps_done: StepsDone
    results_path: Path
