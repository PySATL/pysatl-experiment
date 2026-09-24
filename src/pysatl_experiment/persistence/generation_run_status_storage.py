"""Pipeline status adapter for generation-only runs."""

from pysatl_experiment.persistence.generated_samples_storage import GeneratedSamplesStorage


class GenerationRunStatusStorage:
    """Expose a generation run through the pipeline status contract.

    ``generation_only`` has no execution or report-building stages, so calling
    either corresponding method indicates an invalid pipeline configuration.
    """

    def __init__(self, storage: GeneratedSamplesStorage) -> None:
        self._storage = storage

    def set_generation_done(self, experiment_id: int) -> None:
        """Mark the resolved generation run as complete."""
        self._storage.mark_run_complete(experiment_id)

    def set_execution_done(self, experiment_id: int) -> None:
        """Reject completion updates for a stage generation-only does not have."""
        raise RuntimeError("Generation-only experiments do not have an execution step")

    def set_report_building_done(self, experiment_id: int) -> None:
        """Reject completion updates for a stage generation-only does not have."""
        raise RuntimeError("Generation-only experiments do not have a report-building step")
