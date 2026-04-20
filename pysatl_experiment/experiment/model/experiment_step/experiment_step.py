from abc import ABC, abstractmethod


class IExperimentStep(ABC):
    """
    Interface for experiment step.
    """

    @abstractmethod
    def run(self) -> None:
        pass
