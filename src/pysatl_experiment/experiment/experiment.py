"""Experiment orchestration logic."""

from line_profiler import profile

from src.pysatl_experiment.experiment.experiment_steps import ExperimentSteps
from src.pysatl_experiment.experiment.model.experiment_step import IExperimentStep


class Experiment:
    """Experiment runner."""

    def __init__(self, experiment_steps: ExperimentSteps) -> None:
        """
        Initialize experiment.

        Parameters
        ----------
        experiment_steps : ExperimentSteps
            Experiment step configuration and dependencies.
        """
        self.experiment_steps = experiment_steps

    @profile
    def run_experiment(self) -> None:
        """
        Execute all enabled experiment steps.

        Steps are executed sequentially:
        generation -> execution -> report building.

        After each successful step, the corresponding status
        is saved into experiment storage.
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
            print("Generation step finished.")

        if execution_step is not None:
            print("Running execution step...")
            execution_step.run()
            experiment_storage.set_execution_done(experiment_id)
            print("Execution step finished.")

        if report_building_step is not None:
            print("Running report building step...")
            report_building_step.run()
            experiment_storage.set_report_building_done(experiment_id)
            print("Report building step finished.")
