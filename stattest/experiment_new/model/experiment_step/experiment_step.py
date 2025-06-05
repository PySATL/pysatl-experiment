from typing import Protocol


class IExperimentStep(Protocol):
    """
    Interface for experiment step.
    """

    def run(self) -> None:
        pass
