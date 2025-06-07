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

        if generation_step is not None:
            print("Running generation step...")
            generation_step.run()
            print("Generation step finished")

        if execution_step is not None:
            print("Running execution step...")
            execution_step.run()
            print("Execution step finished")

        print("Running report building step...")
        report_building_step.run()
        print("Report building step finished")
