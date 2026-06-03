"""Base experiment data model."""

from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

from pysatl_experiment.configuration.experiment_config.experiment_config import ExperimentConfig
from pysatl_experiment.configuration.experiment_data.common.steps_done.steps_done import StepsDone


C = TypeVar("C", bound=ExperimentConfig)


@dataclass
class ExperimentData(Generic[C]):
    """
    Serializable experiment data container.

    Attributes
    ----------
    name : str
        Experiment identifier.
    config : C
        Experiment configuration object.
    steps_done : StepsDone
        Information about completed experiment stages.
    results_path : Path
        Experiment result artifacts path.
    """

    name: str
    config: C
    steps_done: StepsDone
    results_path: Path
