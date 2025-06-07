from dataclasses import dataclass

from stattest.experiment_new.model.experiment_step.experiment_step import IExperimentStep


@dataclass
class ExperimentSteps:
    """
    Experiment steps dataclass.
    """

    generation_step: IExperimentStep | None
    execution_step: IExperimentStep | None
    report_building_step: IExperimentStep | None
