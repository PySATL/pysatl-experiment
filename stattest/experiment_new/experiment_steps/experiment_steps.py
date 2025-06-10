from dataclasses import dataclass

from stattest.experiment_new.model.experiment_step.experiment_step import IExperimentStep
from stattest.persistence.model.experiment.experiment import IExperimentStorage


@dataclass
class ExperimentSteps:
    """
    Experiment steps dataclass.
    """

    experiment_id: int
    experiment_storage: IExperimentStorage
    generation_step: IExperimentStep | None
    execution_step: IExperimentStep | None
    report_building_step: IExperimentStep | None
