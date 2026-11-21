"""Experiment orchestration logic."""

import logging

from line_profiler import profile

from pysatl_experiment.experiment_execution.experiment_steps import ExperimentSteps
from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.loggers.context import ExperimentContextAdapter


logger = logging.getLogger(__name__)


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

        log = ExperimentContextAdapter(logger, {"experiment_id": experiment_id})

        if generation_step is not None:
            log.info("Running generation step...", extra={"step": "generation"})
            generation_step.run()
            experiment_storage.set_generation_done(experiment_id)
            log.info("Generation step finished.", extra={"step": "generation"})

        if execution_step is not None:
            log.info("Running execution step...", extra={"step": "execution"})
            execution_step.run()
            experiment_storage.set_execution_done(experiment_id)
            log.info("Execution step finished.", extra={"step": "execution"})

        if report_building_step is not None:
            log.info("Running report building step...", extra={"step": "report_building"})
            report_building_step.run()
            experiment_storage.set_report_building_done(experiment_id)
            log.info("Report building step finished.", extra={"step": "report_building"})
