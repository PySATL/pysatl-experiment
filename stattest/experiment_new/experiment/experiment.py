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

        generation_step: IExperimentStep | None = self.experiment_steps.generation_step
        execution_step: IExperimentStep | None = self.experiment_steps.execution_step
        report_building_step: IExperimentStep | None = self.experiment_steps.report_building_step
        experiment_id = self.experiment_steps.experiment_id
        experiment_storage = self.experiment_steps.experiment_storage

        if generation_step is not None:
            print("Running generation step...")
            generation_step.run()
            experiment_storage.set_generation_done(experiment_id)
            print("Generation step finished")

        if execution_step is not None:
            print("Running execution step...")
            execution_step.run()
            experiment_storage.set_execution_done(experiment_id)
            print("Execution step finished")

        if report_building_step is not None:
            print("Running report building step...")
            report_building_step.run()
            experiment_storage.set_report_building_done(experiment_id)
            print("Report building step finished")
