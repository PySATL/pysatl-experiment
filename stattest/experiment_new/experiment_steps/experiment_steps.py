from dataclasses import dataclass

from stattest.experiment_new.model.experiment_step.experiment_step import IExperimentStep


@dataclass
class ExperimentSteps:
    """
    Experiment steps dataclass.
    """
    generation_step: IExperimentStep
    execution_step: IExperimentStep
    report_building_step: IExperimentStep
