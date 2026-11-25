"""Base experiment data model."""

from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

from pysatl_experiment.configuration.models.steps_status import StepsStatus


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
    steps_status : StepsStatus
        Lifecycle statuses of experiment steps.
    results_path : Path
        Experiment result artifacts path.
    """

    experiment_name: str
    config: C
    steps_status: StepsStatus
    results_path: Path

    @property
    def name(self) -> str:
        """Backward-compatible alias for experiment_name."""
        return self.experiment_name
