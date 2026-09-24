"""Factory for generation-only experiment pipelines."""

import hashlib
import json

from pysatl_experiment.configuration.experiment_config.generation_only import GenerationOnlyExperimentConfig
from pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData
from pysatl_experiment.configuration.models.run_mode import RunMode
from pysatl_experiment.experiment_execution.experiment_steps import ExperimentSteps
from pysatl_experiment.experiment_execution.step.generation_only import GenerationOnlyStep, GenerationOnlyStepData
from pysatl_experiment.persistence.generated_samples_storage import GeneratedSamplesStorage
from pysatl_experiment.persistence.generation_run_status_storage import GenerationRunStatusStorage
from pysatl_experiment.persistence.models.generated_samples import GenerationRunModel


class GenerationOnlyExperimentFactory:
    """Build a one-step pipeline for labelled sample generation."""

    def __init__(self, experiment_data: ExperimentData[GenerationOnlyExperimentConfig]) -> None:
        self._experiment_data = experiment_data

    def create_experiment_steps(self) -> ExperimentSteps:
        """Create a pipeline whose only executable step is sample generation."""
        config = self._experiment_data.config
        storage = GeneratedSamplesStorage(config.storage_connection)
        storage.init()

        fingerprint = self._fingerprint()
        existing_run = storage.get_run_by_fingerprint(fingerprint)
        if config.run_mode is RunMode.OVERWRITE and existing_run is not None:
            if existing_run.id is None:
                raise RuntimeError("Persisted generation run has no id")
            storage.delete_run(existing_run.id)
            existing_run = None

        run_id = storage.create_run(
            GenerationRunModel(
                name=self._experiment_data.experiment_name,
                distribution=config.distribution.value,
                sample_sizes=config.sample_sizes,
                samples_count=config.samples_count,
                parameter_config=config.parameter_config,
                seed=config.seed,
                config_fingerprint=fingerprint,
            )
        )
        generation_step = None
        if existing_run is None or not existing_run.is_complete:
            generation_step = GenerationOnlyStep(
                GenerationOnlyStepData(
                    generation_run_id=run_id,
                    distribution=config.distribution,
                    sample_sizes=config.sample_sizes,
                    samples_count=config.samples_count,
                    parameter_config=config.parameter_config,
                    seed=config.seed,
                    parallel_workers=config.parallel_workers,
                ),
                storage,
            )

        return ExperimentSteps(
            experiment_id=run_id,
            experiment_storage=GenerationRunStatusStorage(storage),
            generation_step=generation_step,
            execution_step=None,
            report_building_step=None,
        )

    def _fingerprint(self) -> str:
        config = self._experiment_data.config
        payload = {
            "name": self._experiment_data.experiment_name,
            "distribution": config.distribution.value,
            "sample_sizes": config.sample_sizes,
            "samples_count": config.samples_count,
            "parameter_config": config.parameter_config,
            "seed": config.seed,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()
