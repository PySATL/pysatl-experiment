from typing import Protocol, TypeVar

from stattest.experiment_new.experiment_steps.experiment_steps import ExperimentSteps
from stattest.experiment_new.model.experiment_step.experiment_step import IExperimentStep

G = TypeVar("G", covariant=True, bound=IExperimentStep)
E = TypeVar("E", covariant=True, bound=IExperimentStep)
R = TypeVar("R", covariant=True, bound=IExperimentStep)


class IAbstractExperimentFactory(Protocol[G, E, R]):
    """
    Abstract experiment factory interface.
    """
    pass

    def create_experiment_steps(self) -> ExperimentSteps:
        """
        Create experiment steps.
        """
        pass

    def _create_generation_step(self) -> G:
        """
        Create generation step.
        """
        pass

    def _create_execution_step(self) -> E:
        """
        Create execution step.
        """
        pass

    def _create_report_building_step(self) -> R:
        """
        Create report building step.
        """
        pass
