"""Experiment step container definitions."""

from dataclasses import dataclass

from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.persistence.contracts.experiment import IExperimentStorage


@dataclass
class ExperimentSteps:
    """
    Container with experiment execution steps.

    Attributes
    ----------
    experiment_name : str
        Experiment identifier in storage.
    experiment_storage : IExperimentStorage
        Experiment metadata storage.
    generation_step : IExperimentStep | None
        Data generation step.
    execution_step : IExperimentStep | None
        Experiment execution step.
    report_building_step : IExperimentStep | None
        Report generation step.
    """

    experiment_name: str
    experiment_storage: IExperimentStorage
    generation_step: IExperimentStep | None
    execution_step: IExperimentStep | None
    report_building_step: IExperimentStep | None
