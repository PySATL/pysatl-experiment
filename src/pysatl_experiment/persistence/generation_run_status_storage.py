"""Pipeline status adapter for generation-only runs."""

from pysatl_experiment.configuration.models.step_status import ExperimentStep, StepStatus
from pysatl_experiment.persistence.generated_samples_storage import GeneratedSamplesStorage


class GenerationRunStatusStorage:
    """Expose a generation run through the pipeline status contract.

    ``generation_only`` has no execution or report-building stages, so calling
    the method with either corresponding step indicates an invalid pipeline
    configuration.

    The generation runs table tracks completion only, so statuses other than
    ``DONE`` have no persistent representation yet.
    """

    def __init__(self, storage: GeneratedSamplesStorage) -> None:
        self._storage = storage

    def set_step_status(self, run_id: int, step: ExperimentStep, status: StepStatus) -> None:
        """Update the generation run status, rejecting unknown pipeline steps."""
        if step is not ExperimentStep.GENERATION:
            raise RuntimeError(f"Generation-only experiments do not have the {step.value} step")
        if status is StepStatus.DONE:
            self._storage.mark_run_complete(run_id)
