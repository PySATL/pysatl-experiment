"""Experiment step container definitions."""

from dataclasses import dataclass

from pysatl_experiment.experiment.model.experiment_step.experiment_step import IExperimentStep
from pysatl_experiment.persistence.model.experiment.experiment import IExperimentStorage


@dataclass
class ExperimentSteps:
    """
    Container with experiment execution steps.

    Attributes
    ----------
    experiment_id : int
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

    experiment_id: int
    experiment_storage: IExperimentStorage
    generation_step: IExperimentStep | None
    execution_step: IExperimentStep | None
    report_building_step: IExperimentStep | None
