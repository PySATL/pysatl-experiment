"""Tests for sample generation configuration model."""

from dataclasses import asdict, fields, is_dataclass, replace
from typing import get_type_hints

import pytest
from pysatl_criterion import DistributionType

from pysatl_experiment.configuration.generation_config import GenerationConfig
from pysatl_experiment.configuration.models.step_type import StepType


def make_config(**overrides: object) -> GenerationConfig:
    """Build a fully populated generation config, overriding selected fields."""
    values: dict[str, object] = {
        "samples_count": 100,
        "generator_type": StepType.STANDARD,
        "distribution_type": DistributionType.NORMAL,
        "distribution_params": {"mean": 0.0, "std": 1.0},
        "sample_sizes": [10, 20],
        "parallel_workers": 4,
    }
    values.update(overrides)

    return GenerationConfig(**values)  # type: ignore[arg-type]


# Checks that a config stores every provided field as-is.
def test_creation_with_valid_fields() -> None:
    config = make_config()

    assert config.samples_count == 100
    assert config.generator_type is StepType.STANDARD
    assert config.distribution_type is DistributionType.NORMAL
    assert config.distribution_params == {"mean": 0.0, "std": 1.0}
    assert config.sample_sizes == [10, 20]
    assert config.parallel_workers == 4


# Checks that every enum member of StepType is accepted as a generator type.
@pytest.mark.parametrize("step_type", list(StepType))
def test_creation_with_every_step_type(step_type: StepType) -> None:
    assert make_config(generator_type=step_type).generator_type is step_type


# Checks that every enum member of DistributionType is accepted.
@pytest.mark.parametrize("distribution_type", list(DistributionType))
def test_creation_with_every_distribution_type(distribution_type: DistributionType) -> None:
    assert make_config(distribution_type=distribution_type).distribution_type is distribution_type


# Checks that positional and keyword construction produce equal configs.
def test_positional_and_keyword_construction_are_equivalent() -> None:
    positional = GenerationConfig(
        50,
        StepType.CUSTOM,
        DistributionType.UNIFORM,
        {"a": 0.0, "b": 1.0},
        [5],
        2,
    )
    keyword = make_config(
        samples_count=50,
        generator_type=StepType.CUSTOM,
        distribution_type=DistributionType.UNIFORM,
        distribution_params={"a": 0.0, "b": 1.0},
        sample_sizes=[5],
        parallel_workers=2,
    )

    assert positional == keyword


# Checks that all six fields are required and omitting one raises a TypeError.
@pytest.mark.parametrize(
    "missing_field",
    ["samples_count", "generator_type", "distribution_type", "distribution_params", "sample_sizes", "parallel_workers"],
)
def test_omitting_required_field_raises_type_error(missing_field: str) -> None:
    values: dict[str, object] = {
        "samples_count": 10,
        "generator_type": StepType.STANDARD,
        "distribution_type": DistributionType.NORMAL,
        "distribution_params": {},
        "sample_sizes": [1],
        "parallel_workers": 1,
    }
    values.pop(missing_field)

    with pytest.raises(TypeError):
        GenerationConfig(**values)  # type: ignore[arg-type]


# Checks that the model declares exactly the six documented dataclass fields with their types.
def test_declares_expected_dataclass_fields() -> None:
    assert is_dataclass(GenerationConfig)
    assert [field.name for field in fields(GenerationConfig)] == [
        "samples_count",
        "generator_type",
        "distribution_type",
        "distribution_params",
        "sample_sizes",
        "parallel_workers",
    ]
    assert get_type_hints(GenerationConfig) == {
        "samples_count": int,
        "generator_type": StepType,
        "distribution_type": DistributionType,
        "distribution_params": dict[str, float],
        "sample_sizes": list[int],
        "parallel_workers": int,
    }


# Checks that two configs with identical field values compare equal.
def test_equality_for_identical_values() -> None:
    assert make_config() == make_config()


# Checks that configs differing in any single field compare unequal.
@pytest.mark.parametrize(
    ("left", "right"),
    [
        (make_config(samples_count=1), make_config(samples_count=2)),
        (make_config(generator_type=StepType.CUSTOM), make_config()),
        (make_config(distribution_type=DistributionType.UNIFORM), make_config()),
        (make_config(parallel_workers=8), make_config()),
        (make_config(sample_sizes=[1, 2, 3]), make_config()),
    ],
)
def test_inequality_for_any_different_field(left: GenerationConfig, right: GenerationConfig) -> None:
    assert left != right


# Checks that the generated repr contains the class name and field values.
def test_repr_contains_field_values() -> None:
    representation = repr(make_config(samples_count=7, parallel_workers=3))

    assert representation.startswith("GenerationConfig(")
    assert "7" in representation
    assert "standard" in representation
    assert "normal" in representation


# Checks that asdict converts the config into a plain field-to-value mapping.
def test_asdict_returns_plain_field_mapping() -> None:
    config = make_config(samples_count=3, parallel_workers=1, sample_sizes=[4])

    assert asdict(config) == {
        "samples_count": 3,
        "generator_type": StepType.STANDARD,
        "distribution_type": DistributionType.NORMAL,
        "distribution_params": {"mean": 0.0, "std": 1.0},
        "sample_sizes": [4],
        "parallel_workers": 1,
    }


# Checks that replace returns an updated copy and leaves the original config untouched.
def test_replace_returns_updated_copy() -> None:
    config = make_config(samples_count=5)

    updated = replace(config, samples_count=6, parallel_workers=2)

    assert updated == make_config(samples_count=6, parallel_workers=2)
    assert config.samples_count == 5


# Checks that config fields can be reassigned after construction.
def test_fields_are_mutable_after_creation() -> None:
    config = make_config()

    config.samples_count = 999
    config.parallel_workers = 16
    config.distribution_type = DistributionType.CAUCHY

    assert config.samples_count == 999
    assert config.parallel_workers == 16
    assert config.distribution_type is DistributionType.CAUCHY


# Checks that mutable configs are not hashable by default.
def test_config_is_not_hashable() -> None:
    with pytest.raises(TypeError):
        hash(make_config())


# Checks that container fields keep the exact objects passed by the caller.
def test_container_fields_keep_references() -> None:
    params = {"mean": 1.0}
    sizes = [1, 2]

    config = make_config(distribution_params=params, sample_sizes=sizes)

    assert config.distribution_params is params
    assert config.sample_sizes is sizes


# Checks that unusual numeric values are stored without any validation logic.
@pytest.mark.parametrize(("samples_count", "parallel_workers"), [(0, 0), (-1, -1), (10**6, 10**3)])
def test_numeric_values_are_not_validated(samples_count: int, parallel_workers: int) -> None:
    config = make_config(samples_count=samples_count, parallel_workers=parallel_workers)

    assert config.samples_count == samples_count
    assert config.parallel_workers == parallel_workers


# Checks that enum fields accept arbitrary raw values without runtime type checking.
def test_enum_fields_accept_arbitrary_values() -> None:
    config = make_config(generator_type="standard", distribution_type="normal")

    assert config.generator_type == "standard"
    assert config.distribution_type == "normal"
