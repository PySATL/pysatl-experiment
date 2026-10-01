"""Tests for adapting generation-only input into execution data."""

from pathlib import Path

from pysatl_criterion import DistributionType

from pysatl_experiment.cli.validation.commands.build_and_run import validate_build_and_run
from pysatl_experiment.configuration.experiment_config.generation_only import GenerationOnlyExperimentConfig
from pysatl_experiment.configuration.models.experiment_type import ExperimentType


def test_validate_generation_only_builds_domain_config_without_cv_fields(tmp_path: Path) -> None:
    raw = {
        "name": "normal_training_samples",
        "config": {
            "experiment_type": "generation_only",
            "distribution": "normal",
            "sample_sizes": [10],
            "samples_count": 3,
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

    assert isinstance(data.config, GenerationOnlyExperimentConfig)
    assert data.config.experiment_type is ExperimentType.GENERATION_ONLY
    assert data.config.distribution is DistributionType.NORMAL
    assert data.config.parameter_config["mean"]["type"] == "random_uniform"
    assert data.config.samples_count == 3
