"""Base experiment data model."""

from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

from pysatl_experiment.configuration.models.steps_done import StepsDone


C = TypeVar("C")


@dataclass
class ExperimentData(Generic[C]):
    """
    Serializable experiment data container.

    Attributes
    ----------
    experiment_name : str
        Experiment identifier.
    config : C
        Experiment configuration object.
    steps_done : StepsDone
        Information about completed experiment stages.
    results_path : Path
        Experiment result artifacts path.
    """

    experiment_name: str
    config: C
    steps_done: StepsDone
    results_path: Path

    @property
    def name(self) -> str:
        """Backward-compatible alias for experiment_name."""
        return self.experiment_name
