"""Tests for the experiment configuration Pydantic schema models."""

from __future__ import annotations

import math
from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from pysatl_criterion import DistributionType
from pysatl_criterion.utils.distribution import get_available_distribution_descriptor

from pysatl_experiment.cli.validation.schemas.criteria import Criterion
from pysatl_experiment.cli.validation.schemas.experiment import (
    BaseExperimentConfig,
    CriticalValueConfig,
    ExperimentConfig,
    FixedParameter,
    GenerationOnlyConfig,
    PowerConfig,
    RandomUniformParameter,
    TimeComplexityConfig,
)
from pysatl_experiment.configuration.models.report_mode import ReportMode
from pysatl_experiment.configuration.models.run_mode import RunMode
from pysatl_experiment.configuration.models.step_type import StepType


def base_config_data(**overrides: Any) -> dict[str, Any]:
    """Build a fully valid raw configuration mapping for the base model."""
    data: dict[str, Any] = {
        "hypothesis": "normal",
        "run_mode": RunMode.REUSE,
        "report_mode": ReportMode.WITHOUT_CHART,
        "generator_type": StepType.STANDARD,
        "executor_type": StepType.STANDARD,
        "report_builder_type": StepType.STANDARD,
        "criteria": [{"criterion_code": "KS"}],
        "storage_connection": "sqlite:///experiment.sqlite",
        "sample_sizes": [10, 20],
        "monte_carlo_count": 100,
        "parallel_workers": 2,
    }
    data.update(overrides)
    return data


def power_config_data(**overrides: Any) -> dict[str, Any]:
    """Build a fully valid raw mapping for a power configuration."""
    data = base_config_data(experiment_type="power", alternatives=[], significance_levels=[0.05])
    data.update(overrides)
    return data


def make_checker(exists: bool = True) -> MagicMock:
    """Build a critical value checker mock returning the requested result."""
    checker = MagicMock()
    checker.check_exists.return_value = exists
    return checker


# Checks that a fully valid base configuration is accepted and stores all fields.
def test_base_config_accepts_valid_input() -> None:
    config = BaseExperimentConfig(**base_config_data())

    assert config.hypothesis is DistributionType.NORMAL
    assert config.run_mode is RunMode.REUSE
    assert config.report_mode is ReportMode.WITHOUT_CHART
    assert config.generator_type is StepType.STANDARD
    assert config.executor_type is StepType.STANDARD
    assert config.report_builder_type is StepType.STANDARD
    assert config.storage_connection == "sqlite:///experiment.sqlite"
    assert config.sample_sizes == [10, 20]
    assert config.monte_carlo_count == 100
    assert config.parallel_workers == 2
    assert config.criteria == [Criterion(criterion_code="KS")]


# Checks that plain string values are coerced into the matching enums.
@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        pytest.param("run_mode", "reuse", RunMode.REUSE, id="run-mode"),
        pytest.param("report_mode", "without-chart", ReportMode.WITHOUT_CHART, id="report-mode"),
        pytest.param("generator_type", "standard", StepType.STANDARD, id="generator-type"),
        pytest.param("executor_type", "standard", StepType.STANDARD, id="executor-type"),
        pytest.param("report_builder_type", "standard", StepType.STANDARD, id="report-builder-type"),
    ],
)
def test_base_config_coerces_string_enums(field: str, value: str, expected: Any) -> None:
    config = BaseExperimentConfig(**base_config_data(**{field: value}))

    assert getattr(config, field) is expected


# Checks that CUSTOM step types are rejected for every core pipeline step.
@pytest.mark.parametrize("field", ["generator_type", "executor_type", "report_builder_type"])
def test_base_config_rejects_custom_step_type(field: str) -> None:
    with pytest.raises(ValidationError, match="is not valid"):
        BaseExperimentConfig(**base_config_data(**{field: StepType.CUSTOM}))


# Checks that sample sizes below the minimum are rejected.
@pytest.mark.parametrize("sample_sizes", [[9], [5, 100], [10, 9, 30]])
def test_base_config_rejects_small_sample_sizes(sample_sizes: list[int]) -> None:
    with pytest.raises(ValidationError, match="Sample sizes must be greater than 10."):
        BaseExperimentConfig(**base_config_data(sample_sizes=sample_sizes))


# Checks that the minimum sample size boundary is accepted.
@pytest.mark.parametrize("sample_sizes", [[10], [10, 20]])
def test_base_config_accepts_minimum_sample_size(sample_sizes: list[int]) -> None:
    config = BaseExperimentConfig(**base_config_data(sample_sizes=sample_sizes))

    assert config.sample_sizes == sample_sizes


# Checks that Monte Carlo counts below the minimum are rejected.
def test_base_config_rejects_low_monte_carlo_count() -> None:
    with pytest.raises(ValidationError, match="Monte Carlo count must be greater than 100."):
        BaseExperimentConfig(**base_config_data(monte_carlo_count=99))


# Checks that the minimum Monte Carlo count boundary is accepted.
def test_base_config_accepts_minimum_monte_carlo_count() -> None:
    assert BaseExperimentConfig(**base_config_data(monte_carlo_count=100)).monte_carlo_count == 100


# Checks that criteria incompatible with the hypothesis are rejected.
def test_base_config_rejects_incompatible_criteria() -> None:
    with pytest.raises(ValidationError, match="incompatible with hypothesis"):
        BaseExperimentConfig(**base_config_data(criteria=[{"criterion_code": "GINI"}]))


# Checks that criteria compatible with the hypothesis are accepted.
@pytest.mark.parametrize("code", ["KS", "AD", "SW"])
def test_base_config_accepts_compatible_criteria(code: str) -> None:
    config = BaseExperimentConfig(**base_config_data(criteria=[{"criterion_code": code}]))

    assert config.criteria == [Criterion(criterion_code=code)]


# Checks that omitting a required field raises a validation error.
@pytest.mark.parametrize("missing", ["hypothesis", "run_mode", "criteria", "storage_connection", "sample_sizes"])
def test_base_config_requires_fields(missing: str) -> None:
    data = base_config_data()
    data.pop(missing)

    with pytest.raises(ValidationError):
        BaseExperimentConfig(**data)


# Checks that building a power config without validation context fails.
def test_power_config_requires_checker_context() -> None:
    with pytest.raises(ValidationError, match="CriticalValueChecker must be provided"):
        PowerConfig.model_validate(power_config_data())


# Checks that a None checker triggers the storage connection guard.
def test_power_config_rejects_none_checker() -> None:
    with pytest.raises(ValidationError, match="storage_connection must be set"):
        PowerConfig.model_validate(power_config_data(), context={"critical_value_checker": None})


# Checks that a power config is accepted when all critical values exist.
def test_power_config_accepts_existing_critical_values() -> None:
    checker = make_checker(exists=True)

    config = PowerConfig.model_validate(
        power_config_data(sample_sizes=[10]),
        context={"critical_value_checker": checker},
    )

    assert isinstance(config, PowerConfig)
    assert config.experiment_type == "power"
    assert config.significance_levels == [0.05]
    assert checker.check_exists.call_count == 1


# Checks that missing critical values produce a descriptive error.
def test_power_config_rejects_missing_critical_values() -> None:
    checker = make_checker(exists=False)

    with pytest.raises(ValidationError, match="Power experiment cannot be run"):
        PowerConfig.model_validate(power_config_data(), context={"critical_value_checker": checker})


# Checks that hypotheses outside the name map are rejected.
def test_power_config_rejects_unknown_hypothesis_for_criterion_name() -> None:
    with pytest.raises(ValidationError, match="Unknown hypothesis 'UNIFORM'"):
        PowerConfig.model_validate(
            power_config_data(hypothesis="uniform"),
            context={"critical_value_checker": make_checker()},
        )


# Checks that the checker is consulted for every criterion/sample-size pair.
def test_power_config_checks_every_criterion_sample_pair() -> None:
    checker = make_checker(exists=True)

    PowerConfig.model_validate(
        power_config_data(
            criteria=[{"criterion_code": "KS"}, {"criterion_code": "AD"}],
            sample_sizes=[10, 20, 30],
        ),
        context={"critical_value_checker": checker},
    )

    assert checker.check_exists.call_count == 6


# Checks that the criterion name passed to the checker follows the expected convention.
def test_power_config_builds_criterion_full_name() -> None:
    checker = make_checker(exists=True)

    PowerConfig.model_validate(
        power_config_data(criteria=[{"criterion_code": "ks"}], sample_sizes=[15]),
        context={"critical_value_checker": checker},
    )

    checker.check_exists.assert_called_once_with("KS_NORMALITY_GOODNESS_OF_FIT", 15)


# Checks that criterion objects (not dicts) are also accepted by the power validator.
def test_power_config_accepts_criterion_objects() -> None:
    checker = make_checker(exists=True)

    PowerConfig.model_validate(
        power_config_data(criteria=[Criterion(criterion_code="KS")], sample_sizes=[10]),
        context={"critical_value_checker": checker},
    )

    checker.check_exists.assert_called_once_with("KS_NORMALITY_GOODNESS_OF_FIT", 10)


# Checks that a missing context key is treated like a missing context.
def test_power_config_requires_checker_key_in_context() -> None:
    with pytest.raises(ValidationError, match="CriticalValueChecker must be provided"):
        PowerConfig.model_validate(power_config_data(), context={"something_else": object()})


# Checks that a critical value config is accepted with its discriminator value.
def test_critical_value_config_accepts_valid_input() -> None:
    config = CriticalValueConfig(**base_config_data(experiment_type="critical_value", significance_levels=[0.01, 0.05]))

    assert config.experiment_type == "critical_value"
    assert config.significance_levels == [0.01, 0.05]


# Checks that a time complexity config is accepted with its discriminator value.
def test_time_complexity_config_accepts_valid_input() -> None:
    config = TimeComplexityConfig(**base_config_data(experiment_type="time_complexity"))

    assert config.experiment_type == "time_complexity"


# Checks that an unknown experiment type is rejected by the literal discriminator.
def test_critical_value_config_rejects_unknown_experiment_type() -> None:
    with pytest.raises(ValidationError):
        CriticalValueConfig(**base_config_data(experiment_type="unknown", significance_levels=[0.05]))


def make_experiment_config(**overrides: Any) -> ExperimentConfig:
    """Build a valid experiment config wrapping a critical value configuration."""
    data: dict[str, Any] = {
        "name": "my_experiment",
        "config": base_config_data(experiment_type="critical_value", significance_levels=[0.05]),
    }
    data.update(overrides)
    return ExperimentConfig(**data)


# Checks that the container stores the name and builds the discriminated config.
def test_experiment_config_accepts_valid_input() -> None:
    config = make_experiment_config()

    assert config.name == "my_experiment"
    assert isinstance(config.config, CriticalValueConfig)


# Checks that a trailing .json suffix is stripped from the experiment name.
def test_experiment_config_strips_json_suffix() -> None:
    assert make_experiment_config(name="my_experiment.json").name == "my_experiment"


# Checks that reserved Windows device names are rejected.
@pytest.mark.parametrize("name", ["CON", "aux", "NUL", "com1"])
def test_experiment_config_rejects_reserved_names(name: str) -> None:
    with pytest.raises(ValidationError, match="mustn't be"):
        make_experiment_config(name=name)


# Checks that names containing forbidden characters are rejected.
@pytest.mark.parametrize("name", ["a/b", "a\\b", "a:b", "a*b", "a?b", "a<b", "a>b", "a|b", "a b"])
def test_experiment_config_rejects_invalid_characters(name: str) -> None:
    with pytest.raises(ValidationError, match="invalid characters"):
        make_experiment_config(name=name)


# Checks that an empty name is rejected.
def test_experiment_config_rejects_empty_name() -> None:
    with pytest.raises(ValidationError, match="cannot be empty"):
        make_experiment_config(name="")


# Checks that the config field is required.
def test_experiment_config_requires_config() -> None:
    with pytest.raises(ValidationError):
        ExperimentConfig(name="my_experiment")  # type: ignore[call-arg]


# Checks that a power experiment config is accepted when the checker context is provided.
def test_experiment_config_supports_power_config_with_context() -> None:
    config = ExperimentConfig.model_validate(
        {"name": "power_exp", "config": power_config_data()},
        context={"critical_value_checker": make_checker(exists=True)},
    )

    assert isinstance(config.config, PowerConfig)


def generation_only_data(**overrides: Any) -> dict[str, Any]:
    """Build a fully valid raw mapping for a generation-only configuration."""
    data: dict[str, Any] = {
        "experiment_type": "generation_only",
        "distribution": "normal",
        "sample_sizes": [10, 20],
        "samples_count": 5,
        "parameters": {"mean": {"type": "fixed", "value": 0.0}, "var": {"type": "fixed", "value": 1.0}},
        "seed": 7,
        "run_mode": RunMode.REUSE,
        "storage_connection": "sqlite:///generation.sqlite",
    }
    data.update(overrides)
    return data


def distributions_without_metadata() -> tuple[DistributionType, ...]:
    """Collect distributions that do not expose parameter metadata."""
    without_metadata = []
    for distribution in DistributionType:
        try:
            get_available_distribution_descriptor(distribution)
        except StopIteration:
            without_metadata.append(distribution)
    return tuple(without_metadata)


# Checks that finite values are accepted as fixed distribution parameters.
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0.0, id="zero"),
        pytest.param(1.5, id="fraction"),
        pytest.param(-2.25, id="negative"),
    ],
)
def test_fixed_parameter_accepts_finite_value(value: float) -> None:
    parameter = FixedParameter(value=value)

    assert parameter.type == "fixed"
    assert parameter.value == value


# Checks that values unable to describe a finite parameter are rejected.
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(math.nan, id="nan"),
        pytest.param(math.inf, id="positive-infinity"),
        pytest.param(-math.inf, id="negative-infinity"),
    ],
)
def test_fixed_parameter_rejects_non_finite_value(value: float) -> None:
    with pytest.raises(ValidationError, match="parameter value must be finite"):
        FixedParameter(value=value)


# Checks that strictly ordered finite bounds are accepted as uniform parameters.
@pytest.mark.parametrize(
    ("low", "high"),
    [
        pytest.param(-5.0, 5.0, id="symmetric"),
        pytest.param(-1.0, -0.5, id="negative"),
        pytest.param(0.0, 1e-9, id="narrow"),
    ],
)
def test_random_uniform_parameter_accepts_ordered_bounds(low: float, high: float) -> None:
    parameter = RandomUniformParameter(type="random_uniform", low=low, high=high)

    assert parameter.type == "random_uniform"
    assert (parameter.low, parameter.high) == (low, high)


# Checks that non-finite uniform bounds are rejected.
@pytest.mark.parametrize(
    ("low", "high"),
    [
        pytest.param(math.nan, 1.0, id="nan-low"),
        pytest.param(0.0, math.inf, id="inf-high"),
        pytest.param(-math.inf, math.inf, id="both-infinite"),
    ],
)
def test_random_uniform_parameter_rejects_non_finite_bounds(low: float, high: float) -> None:
    with pytest.raises(ValidationError, match="uniform parameter bounds must be finite"):
        RandomUniformParameter(type="random_uniform", low=low, high=high)


# Checks that uniform bounds which are not strictly increasing are rejected.
@pytest.mark.parametrize(
    ("low", "high"),
    [
        pytest.param(1.0, 1.0, id="equal"),
        pytest.param(2.0, 1.0, id="reversed"),
    ],
)
def test_random_uniform_parameter_rejects_unordered_bounds(low: float, high: float) -> None:
    with pytest.raises(ValidationError, match="low must be less than high"):
        RandomUniformParameter(type="random_uniform", low=low, high=high)


# Checks that a generation-only configuration with fixed parameters is accepted.
def test_generation_only_config_accepts_fixed_parameters() -> None:
    config = GenerationOnlyConfig(**generation_only_data())

    assert config.experiment_type == "generation_only"
    assert config.distribution is DistributionType.NORMAL
    assert config.parameters == {"mean": FixedParameter(value=0.0), "var": FixedParameter(value=1.0)}
    assert config.parallel_workers == 1


# Checks that a generation-only configuration with uniform parameters is accepted.
def test_generation_only_config_accepts_uniform_parameters() -> None:
    config = GenerationOnlyConfig(
        **generation_only_data(
            parameters={
                "mean": {"type": "random_uniform", "low": -1.0, "high": 1.0},
                "var": {"type": "fixed", "value": 2.0},
            }
        )
    )

    assert config.parameters == {
        "mean": RandomUniformParameter(type="random_uniform", low=-1.0, high=1.0),
        "var": FixedParameter(value=2.0),
    }


# Checks that a distribution without parameter metadata is reported as unsupported.
def test_generation_only_config_rejects_distribution_without_metadata() -> None:
    unsupported = distributions_without_metadata()

    assert unsupported, "expected at least one distribution without parameter metadata"

    with pytest.raises(ValidationError, match="does not expose parameter metadata"):
        GenerationOnlyConfig(**generation_only_data(distribution=unsupported[0].value))


# Checks that parameters unknown to the distribution descriptor are rejected.
def test_generation_only_config_rejects_unknown_parameter() -> None:
    parameters = {
        "mean": {"type": "fixed", "value": 0.0},
        "var": {"type": "fixed", "value": 1.0},
        "sigma": {"type": "fixed", "value": 1.0},
    }

    with pytest.raises(ValidationError, match=r"Unknown parameters for normal: sigma"):
        GenerationOnlyConfig(**generation_only_data(parameters=parameters))


# Checks that parameters required by the distribution descriptor must be provided.
def test_generation_only_config_rejects_missing_parameter() -> None:
    with pytest.raises(ValidationError, match=r"Missing parameters for normal: var"):
        GenerationOnlyConfig(**generation_only_data(parameters={"mean": {"type": "fixed", "value": 0.0}}))


# Checks that the descriptor validator is applied to both bounds of a parameter rule.
@pytest.mark.parametrize(
    "rule",
    [
        pytest.param({"type": "fixed", "value": -1.0}, id="fixed-negative"),
        pytest.param({"type": "fixed", "value": 0.0}, id="fixed-zero"),
        pytest.param({"type": "random_uniform", "low": -1.0, "high": 1.0}, id="uniform"),
    ],
)
def test_generation_only_config_rejects_constraint_violation(rule: dict[str, Any]) -> None:
    parameters = {"mean": {"type": "fixed", "value": 0.0}, "var": rule}

    with pytest.raises(ValidationError, match=r"normal\.var violates its distribution constraint"):
        GenerationOnlyConfig(**generation_only_data(parameters=parameters))


# Checks that the smallest accepted positive value satisfies the descriptor validator.
def test_generation_only_config_accepts_smallest_positive_parameter() -> None:
    parameters = {"mean": {"type": "fixed", "value": 0.0}, "var": {"type": "fixed", "value": 1e-12}}
    config = GenerationOnlyConfig(**generation_only_data(parameters=parameters))

    assert config.parameters["var"] == FixedParameter(value=1e-12)


# Checks that sample sizes below the minimum are rejected for generation-only runs.
@pytest.mark.parametrize("sample_sizes", [[9], [10, 5]])
def test_generation_only_config_rejects_small_sample_sizes(sample_sizes: list[int]) -> None:
    with pytest.raises(ValidationError, match=r"Sample sizes must be greater than 10\."):
        GenerationOnlyConfig(**generation_only_data(sample_sizes=sample_sizes))


# Checks that repeated sample sizes are rejected for generation-only runs.
@pytest.mark.parametrize("sample_sizes", [[10, 10], [10, 20, 10]])
def test_generation_only_config_rejects_duplicate_sample_sizes(sample_sizes: list[int]) -> None:
    with pytest.raises(ValidationError, match="Sample sizes must be unique"):
        GenerationOnlyConfig(**generation_only_data(sample_sizes=sample_sizes))


# Checks that unique sample sizes starting from the minimum are accepted.
def test_generation_only_config_accepts_unique_sample_sizes() -> None:
    config = GenerationOnlyConfig(**generation_only_data(sample_sizes=[10, 11]))

    assert config.sample_sizes == [10, 11]


# Checks that the container builds a generation-only config from its discriminator.
def test_experiment_config_supports_generation_only_config() -> None:
    config = ExperimentConfig.model_validate({"name": "generation", "config": generation_only_data()})

    assert isinstance(config.config, GenerationOnlyConfig)
    assert config.name == "generation"


# Checks that the config validator guards against a missing configuration object.
def test_experiment_config_check_config_rejects_missing_config() -> None:
    with pytest.raises(ValueError, match="Missing config"):
        ExperimentConfig.check_config(None)


# Checks that the config validator passes a present configuration through unchanged.
def test_experiment_config_check_config_returns_present_config() -> None:
    config = generation_only_data()

    assert ExperimentConfig.check_config(config) is config
