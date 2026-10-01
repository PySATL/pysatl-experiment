"""Tests for executing generation-only data through the CLI pipeline."""

from pathlib import Path

from pysatl_experiment.cli.commands.build_and_run import _run_experiment_data
from pysatl_experiment.cli.validation.commands.build_and_run import validate_build_and_run
from pysatl_experiment.experiment_execution.experiment_factory.generation_only_factory import (
    GenerationOnlyExperimentFactory,
)
from pysatl_experiment.persistence.generated_samples_storage import GeneratedSamplesStorage


def test_run_experiment_data_executes_only_generation_step(tmp_path: Path) -> None:
    raw = {
        "name": "normal_training_samples",
        "config": {
            "experiment_type": "generation_only",
            "distribution": "normal",
            "sample_sizes": [10],
            "samples_count": 2,
            "parameters": {
                "mean": {"type": "random_uniform", "low": -5.0, "high": 5.0},
                "var": {"type": "fixed", "value": 1.0},
            },
            "seed": 42,
            "run_mode": "reuse",
            "storage_connection": f"sqlite:///{tmp_path / 'samples.sqlite'}",
        },
    }
    data = validate_build_and_run(raw)

    _run_experiment_data(data)

    steps = GenerationOnlyExperimentFactory(data).create_experiment_steps()
    assert steps.generation_step is None
    storage = GeneratedSamplesStorage(data.config.storage_connection)
    storage.init()
    assert storage.get_existing_sample_numbers(
        steps.experiment_id,
        sample_size=10,
    ) == {1, 2}
