"""Abstract interfaces for experiment execution steps."""

from abc import ABC, abstractmethod


class IExperimentStep(ABC):  # TODO: structure!!
    """Base interface for experiment pipeline steps.

    Experiment execution is divided into independent stages such as:

    - sample generation,
    - statistical execution,
    - report building.

    Every pipeline step must implement the ``run`` method.
    """

    @abstractmethod
    def run(self) -> None:
        """Execute experiment step."""
        raise NotImplementedError
