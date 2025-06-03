from stattest.experiment_new.experiment_steps.experiment_steps import ExperimentSteps
from stattest.experiment_new.model.experiment_step.experiment_step import IExperimentStep


class Experiment:
    """
    Experiment.
    """

    def __init__(self, experiment_steps: ExperimentSteps):
        self.experiment_steps = experiment_steps

    def run_experiment(self) -> None:
        """
        Run experiment.
        """
        generation_step: IExperimentStep = self.experiment_steps.generation_step
        execution_step: IExperimentStep = self.experiment_steps.execution_step
        report_building_step: IExperimentStep = self.experiment_steps.report_building_step

        generation_step.run()
        execution_step.run()
        report_building_step.run()
