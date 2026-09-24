"""Tests for generation-only experiment assembly."""

from dataclasses import replace
from pathlib import Path

from pysatl_criterion import DistributionType

from pysatl_experiment.configuration.experiment_config.generation_only import GenerationOnlyExperimentConfig
from pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData
from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.configuration.models.run_mode import RunMode
from pysatl_experiment.configuration.models.steps_done import StepsDone
from pysatl_experiment.experiment_execution.experiment import Experiment
from pysatl_experiment.experiment_execution.experiment_factory.generation_only_factory import (
    GenerationOnlyExperimentFactory,
)
from pysatl_experiment.persistence.generated_samples_storage import GeneratedSamplesStorage


def test_factory_creates_reusable_generation_pipeline(tmp_path: Path) -> None:
    database = tmp_path / "samples.sqlite"
    config = GenerationOnlyExperimentConfig(
        experiment_type=ExperimentType.GENERATION_ONLY,
        storage_connection=f"sqlite:///{database}",
        run_mode=RunMode.REUSE,
        distribution=DistributionType.NORMAL,
        sample_sizes=[10],
        samples_count=2,
        parameter_config={
            "mean": {"type": "random_uniform", "low": -5.0, "high": 5.0},
            "var": {"type": "fixed", "value": 1.0},
        },
        seed=42,
        parallel_workers=2,
    )
    data = ExperimentData(
        experiment_name="normal_training_samples",
        config=config,
        steps_done=StepsDone(False, False, False),
        results_path=Path(),
    )

    first_steps = GenerationOnlyExperimentFactory(data).create_experiment_steps()
    Experiment(first_steps).run_experiment()
    second_steps = GenerationOnlyExperimentFactory(data).create_experiment_steps()
    Experiment(second_steps).run_experiment()

    storage = GeneratedSamplesStorage(config.storage_connection)
    storage.init()
    run_id = first_steps.experiment_id
    assert first_steps.generation_step is not None
    assert first_steps.generation_step.step_data.parallel_workers == 2
    assert second_steps.generation_step is None
    assert storage.get_existing_sample_numbers(run_id, sample_size=10) == {1, 2}
    stored_run = storage.get_run(run_id)
    assert stored_run is not None
    assert stored_run.is_complete is True


def test_factory_overwrite_clears_only_matching_generation_run(tmp_path: Path) -> None:
    database = tmp_path / "samples.sqlite"
    reusable_config = GenerationOnlyExperimentConfig(
        experiment_type=ExperimentType.GENERATION_ONLY,
        storage_connection=f"sqlite:///{database}",
        run_mode=RunMode.REUSE,
        distribution=DistributionType.NORMAL,
        sample_sizes=[10],
        samples_count=1,
        parameter_config={
            "mean": {"type": "fixed", "value": 0.0},
            "var": {"type": "fixed", "value": 1.0},
        },
        seed=42,
    )
    data = ExperimentData(
        experiment_name="normal_training_samples",
        config=reusable_config,
        steps_done=StepsDone(False, False, False),
        results_path=Path(),
    )
    Experiment(GenerationOnlyExperimentFactory(data).create_experiment_steps()).run_experiment()

    overwrite_data = replace(data, config=replace(reusable_config, run_mode=RunMode.OVERWRITE))
    replacement_steps = GenerationOnlyExperimentFactory(overwrite_data).create_experiment_steps()

    assert replacement_steps.generation_step is not None
    assert replacement_steps.generation_step.storage.get_existing_sample_numbers(
        replacement_steps.experiment_id,
        sample_size=10,
    ) == set()
