"""Experiment orchestration logic."""

import logging

from line_profiler import profile

from pysatl_experiment.configuration.models.step_status import ExperimentStep, StepStatus
from pysatl_experiment.experiment_execution.experiment_steps import ExperimentSteps
from pysatl_experiment.experiment_execution.step.abstract_experiment_step import IExperimentStep
from pysatl_experiment.loggers.context import ExperimentContextAdapter
from pysatl_experiment.persistence.models.experiment import IExperimentStatusStorage


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

        The step lifecycle status is persisted to experiment storage:
        ``RUNNING`` before the step starts, ``DONE`` after it finishes and
        ``FAILED`` when it raises. Failures are logged with the experiment
        context and re-raised, so subsequent steps are not executed.
        """
        generation_step: IExperimentStep | None = self.experiment_steps.generation_step
        execution_step: IExperimentStep | None = self.experiment_steps.execution_step
        report_building_step: IExperimentStep | None = self.experiment_steps.report_building_step
        experiment_id = self.experiment_steps.experiment_id
        experiment_storage = self.experiment_steps.experiment_storage

        log = ExperimentContextAdapter(logger, {"experiment_id": experiment_id})

        if generation_step is not None:
            self._run_pipeline_step(
                generation_step, ExperimentStep.GENERATION, "generation", experiment_storage, experiment_id, log
            )

        if execution_step is not None:
            self._run_pipeline_step(
                execution_step, ExperimentStep.EXECUTION, "execution", experiment_storage, experiment_id, log
            )

        if report_building_step is not None:
            self._run_pipeline_step(
                report_building_step,
                ExperimentStep.REPORT_BUILDING,
                "report building",
                experiment_storage,
                experiment_id,
                log,
            )

    @staticmethod
    def _run_pipeline_step(
        step: IExperimentStep,
        step_kind: ExperimentStep,
        step_name: str,
        experiment_storage: IExperimentStatusStorage,
        experiment_id: int,
        log: ExperimentContextAdapter,
    ) -> None:
        """
        Run one pipeline step, persisting its lifecycle status.

        Parameters
        ----------
        step : IExperimentStep
            Step to execute.
        step_kind : ExperimentStep
            Pipeline step identifier used for status persistence and
            log context.
        step_name : str
            Human-readable step name used in log messages.
        experiment_storage : IExperimentStatusStorage
            Storage for step lifecycle statuses.
        experiment_id : int
            Experiment identifier.
        log : ExperimentContextAdapter
            Logger carrying the experiment context.

        Raises
        ------
        Exception
            Re-raises any exception raised by the step after recording
            the ``FAILED`` status.
        """
        log.info("Running %s step...", step_name, extra={"step": step_kind.value})
        experiment_storage.set_step_status(experiment_id, step_kind, StepStatus.RUNNING)
        try:
            step.run()
        except Exception:
            experiment_storage.set_step_status(experiment_id, step_kind, StepStatus.FAILED)
            log.exception("%s step failed.", step_name.capitalize(), extra={"step": step_kind.value})
            raise
        experiment_storage.set_step_status(experiment_id, step_kind, StepStatus.DONE)
        log.info("%s step finished.", step_name.capitalize(), extra={"step": step_kind.value})
