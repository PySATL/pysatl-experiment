"""Tests for generation-only experiment configuration."""

import pytest
from pydantic import ValidationError
from pysatl_criterion import DistributionType

from pysatl_experiment.cli.validation.schemas.experiment import ExperimentConfig, GenerationOnlyConfig


def _normal_config() -> dict:
    return {
        "name": "normal_training_samples",
        "config": {
            "experiment_type": "generation_only",
            "distribution": "normal",
            "sample_sizes": [100],
            "samples_count": 10,
            "parameters": {
                "mean": {"type": "random_uniform", "low": -5.0, "high": 5.0},
                "var": {"type": "fixed", "value": 1.0},
            },
            "seed": 42,
            "run_mode": "reuse",
            "storage_connection": "sqlite:///training.sqlite",
        },
    }


def test_generation_only_config_accepts_fixed_and_uniform_parameters() -> None:
    validated = ExperimentConfig.model_validate(_normal_config())

    assert isinstance(validated.config, GenerationOnlyConfig)
    assert validated.config.distribution.value == "normal"
    assert validated.config.parameters["var"].value == 1.0
    assert validated.config.parameters["mean"].low == -5.0
    assert validated.config.parameters["mean"].high == 5.0
    assert validated.config.parallel_workers == 1


def test_generation_only_config_accepts_parallel_workers() -> None:
    raw = _normal_config()
    raw["config"]["parallel_workers"] = 4

    validated = ExperimentConfig.model_validate(raw)

    assert validated.config.parallel_workers == 4


def test_generation_only_config_uses_criterion_descriptor_for_new_distribution() -> None:
    raw = _normal_config()
    raw["config"]["distribution"] = "cauchy"
    raw["config"]["parameters"] = {
        "t": {"type": "fixed", "value": 0.0},
        "s": {"type": "random_uniform", "low": 0.5, "high": 2.0},
    }

    validated = ExperimentConfig.model_validate(raw)

    assert validated.config.distribution is DistributionType.CAUCHY
    assert set(validated.config.parameters) == {"t", "s"}


def test_generation_only_config_applies_descriptor_validator_to_parameter_range() -> None:
    raw = _normal_config()
    raw["config"]["distribution"] = "cauchy"
    raw["config"]["parameters"] = {
        "t": {"type": "fixed", "value": 0.0},
        "s": {"type": "random_uniform", "low": -1.0, "high": 2.0},
    }

    with pytest.raises(ValidationError, match="cauchy.s"):
        ExperimentConfig.model_validate(raw)


def test_generation_only_config_rejects_log_uniform_parameter() -> None:
    raw = _normal_config()
    raw["config"]["parameters"]["var"] = {
        "type": "random_log_uniform",
        "low": 0.01,
        "high": 100.0,
    }

    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(raw)


def test_generation_only_config_does_not_require_criteria_or_report_fields() -> None:
    validated = ExperimentConfig.model_validate(_normal_config())

    dumped = validated.config.model_dump()
    assert "criteria" not in dumped
    assert "executor_type" not in dumped
    assert "report_builder_type" not in dumped


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sample_sizes", []),
        ("sample_sizes", [9]),
        ("samples_count", 0),
        ("seed", -1),
        ("seed", 2**63),
        ("parallel_workers", 0),
    ],
)
def test_generation_only_config_rejects_invalid_run_values(field: str, value: object) -> None:
    raw = _normal_config()
    raw["config"][field] = value

    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(raw)


def test_generation_only_config_rejects_unknown_parameter() -> None:
    raw = _normal_config()
    raw["config"]["parameters"]["sigma"] = {"type": "fixed", "value": 1.0}

    with pytest.raises(ValidationError, match="Unknown parameters for normal: sigma"):
        ExperimentConfig.model_validate(raw)


def test_generation_only_config_rejects_non_positive_variance_range() -> None:
    raw = _normal_config()
    raw["config"]["parameters"]["var"] = {"type": "random_uniform", "low": 0.0, "high": 1.0}

    with pytest.raises(ValidationError, match="normal.var violates its distribution constraint"):
        ExperimentConfig.model_validate(raw)


def test_generation_only_config_rejects_reversed_uniform_parameter_range() -> None:
    raw = _normal_config()
    raw["config"]["parameters"]["mean"] = {"type": "random_uniform", "low": 2.0, "high": 1.0}

    with pytest.raises(ValidationError, match="low must be less than high"):
        ExperimentConfig.model_validate(raw)


def test_generation_only_config_rejects_parameter_without_explicit_type() -> None:
    raw = _normal_config()
    raw["config"]["parameters"]["var"] = 1.0

    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(raw)
