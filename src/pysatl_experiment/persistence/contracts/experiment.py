"""Storage contract for experiment."""

from abc import ABC, abstractmethod

from pysatl_criterion.persistence.models.base import IDataStorage

from pysatl_experiment.persistence.models.experiment import ExperimentModel, ExperimentQuery


class IExperimentStorage(IDataStorage[ExperimentModel, ExperimentQuery], ABC):
    """Experiment configuration storage interface."""

    @abstractmethod
    def set_generation_done(self, experiment_name: str) -> None:
        """
        Mark generation step as completed.

        Parameters
        ----------
        experiment_name : str
        """
        pass

    @abstractmethod
    def set_execution_done(self, experiment_name: str) -> None:
        """
        Mark execution step as completed.

        Parameters
        ----------
        experiment_name : str
        """
        pass

    @abstractmethod
    def set_report_building_done(self, experiment_name: str) -> None:
        """
        Mark report building step as completed.

        Parameters
        ----------
        experiment_name : str
        """
        pass
