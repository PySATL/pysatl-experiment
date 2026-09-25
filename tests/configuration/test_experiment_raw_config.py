"""Tests for raw experiment configuration models."""

from dataclasses import is_dataclass
from typing import Any, get_type_hints

import pytest

from pysatl_experiment.configuration.experiment_raw_config import (
    CriteriaRawConfig,
    CriticalValuesRawConfig,
    ExecutionRawConfig,
    GenerationRawConfig,
    PowerRawConfig,
    RawConfig,
    ReportRawConfig,
    TimeComplexityRawConfig,
)


ANNOTATION_ONLY_MODELS = [GenerationRawConfig, CriteriaRawConfig, ExecutionRawConfig, RawConfig]

MARKER_MODELS = [ReportRawConfig, PowerRawConfig, CriticalValuesRawConfig, TimeComplexityRawConfig]

ALL_MODELS = [*ANNOTATION_ONLY_MODELS, *MARKER_MODELS]


# Checks that GenerationRawConfig declares the six documented fields with their types.
def test_generation_raw_config_type_hints() -> None:
    assert get_type_hints(GenerationRawConfig) == {
        "samples_count": int,
        "generator_type": str,
        "distribution_type": str | None,
        "distribution_params": dict[str, float] | None,
        "sample_sizes": list[int] | None,
        "parallel_workers": int | None,
    }


# Checks that CriteriaRawConfig declares criterion code and parameters as optional.
def test_criteria_raw_config_type_hints() -> None:
    assert get_type_hints(CriteriaRawConfig) == {
        "criterion_code": str | None,
        "parameters": dict[str, Any] | None,
    }


# Checks that ExecutionRawConfig declares the executor, workers and criteria fields.
def test_execution_raw_config_type_hints() -> None:
    assert get_type_hints(ExecutionRawConfig) == {
        "executor_type": str | None,
        "parallel_workers": int | None,
        "criteria": list[CriteriaRawConfig] | None,
    }


# Checks that RawConfig aggregates optional sections of an experiment configuration.
def test_raw_config_type_hints() -> None:
    assert get_type_hints(RawConfig) == {
        "experiment_name": str | None,
        "storage_connection": str | None,
        "experiment_type": str | None,
        "run_mode": str | None,
        "generation": GenerationRawConfig | None,
        "execution": ExecutionRawConfig | None,
        "report": ReportRawConfig | None,
    }


# Checks that marker models carry no annotations at all.
@pytest.mark.parametrize("model", MARKER_MODELS)
def test_marker_models_declare_no_fields(model: type) -> None:
    assert getattr(model, "__annotations__", {}) == {}


# Checks that marker models expose the documented placeholder docstrings.
@pytest.mark.parametrize(
    ("model", "expected_doc"),
    [
        (PowerRawConfig, "Raw configuration for a statistical power experiment."),
        (CriticalValuesRawConfig, "Raw configuration for a critical values experiment."),
        (TimeComplexityRawConfig, "Raw configuration for a time complexity experiment."),
    ],
)
def test_marker_models_have_docstrings(model: type, expected_doc: str) -> None:
    assert expected_doc in (model.__doc__ or "")


# Checks that raw configs are plain classes with no generated dataclass behaviour.
@pytest.mark.parametrize("model", ALL_MODELS)
def test_models_are_not_dataclasses(model: type) -> None:
    assert not is_dataclass(model)
    assert "__init__" not in vars(model)


# Checks that constructing an annotation-only model populates no attributes.
@pytest.mark.parametrize("model", ANNOTATION_ONLY_MODELS)
def test_construction_does_not_populate_attributes(model: type) -> None:
    instance = model()

    assert vars(instance) == {}
    for name in get_type_hints(model):
        assert not hasattr(instance, name)


# Checks that annotation-only models reject positional constructor arguments.
@pytest.mark.parametrize("model", ANNOTATION_ONLY_MODELS)
def test_positional_arguments_are_rejected(model: type) -> None:
    with pytest.raises(TypeError):
        model("unexpected")


# Checks that annotation-only models reject unexpected keyword arguments.
@pytest.mark.parametrize("model", ANNOTATION_ONLY_MODELS)
def test_keyword_arguments_are_rejected(model: type) -> None:
    with pytest.raises(TypeError):
        model(unexpected="value")


# Checks that empty marker models can be instantiated and used as placeholders.
@pytest.mark.parametrize("model", MARKER_MODELS)
def test_marker_models_can_be_instantiated(model: type) -> None:
    instance = model()

    assert isinstance(instance, model)
    assert vars(instance) == {}


# Checks that declared fields accept and keep assigned values.
@pytest.mark.parametrize(
    ("model", "attribute", "value"),
    [
        (GenerationRawConfig, "samples_count", 250),
        (GenerationRawConfig, "distribution_type", "normal"),
        (GenerationRawConfig, "distribution_params", {"mean": 0.0}),
        (GenerationRawConfig, "sample_sizes", [10, 20]),
        (CriteriaRawConfig, "criterion_code", "KS"),
        (CriteriaRawConfig, "parameters", {"alpha": 0.05}),
        (ExecutionRawConfig, "executor_type", "standard"),
        (ExecutionRawConfig, "parallel_workers", 2),
        (RawConfig, "experiment_name", "my-experiment"),
        (RawConfig, "run_mode", "reuse"),
    ],
)
def test_declared_fields_can_be_assigned(model: type, attribute: str, value: object) -> None:
    instance = model()
    setattr(instance, attribute, value)

    assert getattr(instance, attribute) == value


# Checks that optional fields accept None without any validation.
@pytest.mark.parametrize(
    ("model", "attribute"),
    [
        (GenerationRawConfig, "distribution_type"),
        (GenerationRawConfig, "distribution_params"),
        (GenerationRawConfig, "parallel_workers"),
        (CriteriaRawConfig, "criterion_code"),
        (CriteriaRawConfig, "parameters"),
        (ExecutionRawConfig, "executor_type"),
        (ExecutionRawConfig, "parallel_workers"),
        (ExecutionRawConfig, "criteria"),
        (RawConfig, "generation"),
        (RawConfig, "execution"),
        (RawConfig, "report"),
    ],
)
def test_optional_fields_accept_none(model: type, attribute: str) -> None:
    instance = model()
    setattr(instance, attribute, None)

    assert getattr(instance, attribute) is None


# Checks that undeclared attributes may be attached to any raw config instance.
@pytest.mark.parametrize("model", ALL_MODELS)
def test_arbitrary_attributes_are_allowed(model: type) -> None:
    instance = model()
    instance.custom = "value"  # type: ignore[attr-defined]

    assert instance.custom == "value"  # type: ignore[attr-defined]


# Checks that instances do not share state and compare by identity.
@pytest.mark.parametrize("model", ALL_MODELS)
def test_instances_are_distinct_and_not_comparable_by_value(model: type) -> None:
    first = model()
    second = model()

    assert first is not second
    assert first != second

    first.custom = 1  # type: ignore[attr-defined]

    assert not hasattr(second, "custom")


# Checks that the default repr is used because no __repr__ is generated.
@pytest.mark.parametrize("model", ALL_MODELS)
def test_default_repr_contains_class_name(model: type) -> None:
    assert model.__name__ in repr(model())


# Checks that nested raw configs can be composed into a full experiment configuration.
def test_nested_configuration_composition() -> None:
    generation = GenerationRawConfig()
    generation.samples_count = 100
    generation.generator_type = "standard"
    generation.distribution_type = "normal"
    generation.distribution_params = {"mean": 0.0, "std": 1.0}
    generation.sample_sizes = [10, 50]
    generation.parallel_workers = 1

    criteria = CriteriaRawConfig()
    criteria.criterion_code = "KS"
    criteria.parameters = None

    execution = ExecutionRawConfig()
    execution.executor_type = "standard"
    execution.parallel_workers = 4
    execution.criteria = [criteria]

    raw = RawConfig()
    raw.experiment_name = "experiment"
    raw.storage_connection = "sqlite:///pysatl.sqlite"
    raw.experiment_type = "critical_value"
    raw.run_mode = "reuse"
    raw.generation = generation
    raw.execution = execution
    raw.report = ReportRawConfig()

    assert raw.generation is generation
    assert raw.execution.criteria == [criteria]
    assert isinstance(raw.report, ReportRawConfig)
    assert vars(raw)["experiment_name"] == "experiment"
