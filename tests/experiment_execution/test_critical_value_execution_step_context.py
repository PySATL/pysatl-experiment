"""Tests for the critical value execution step context container."""

from dataclasses import asdict, fields, is_dataclass
from typing import get_type_hints
from unittest.mock import MagicMock

import pytest

from pysatl_experiment.experiment_execution.step.execution_step.critical_value import (
    critical_value_execution_step_context,
)
from pysatl_experiment.experiment_execution.step.generation_step.generation_step_context import GenerationData


CriticalValueExecutionStepContext = critical_value_execution_step_context.CriticalValueExecutionStepContext


def make_generation_data(sample_size: int = 10) -> GenerationData:
    """Build a generation data entry with a mocked generator."""
    return GenerationData(generator=MagicMock(), sample_size=sample_size, samples_count=100)


def make_context(**overrides: object) -> CriticalValueExecutionStepContext:
    """Build a fully populated context, overriding selected fields."""
    values: dict[str, object] = {
        "data_list": [make_generation_data(10), make_generation_data(20)],
        "experiment_name": "cv_experiment",
    }
    values.update(overrides)

    return CriticalValueExecutionStepContext(**values)  # type: ignore[arg-type]


# Checks that the container is a dataclass.
def test_container_is_a_dataclass() -> None:
    assert is_dataclass(CriticalValueExecutionStepContext)
    assert is_dataclass(make_context())


# Checks that both provided fields are stored as-is.
def test_creation_stores_fields() -> None:
    data_list = [make_generation_data(5)]
    context = make_context(data_list=data_list, experiment_name="named_experiment")

    assert context.data_list is data_list
    assert context.experiment_name == "named_experiment"


# Checks that the dataclass declares exactly the documented fields and types.
def test_declares_expected_fields() -> None:
    assert {field.name for field in fields(CriticalValueExecutionStepContext)} == {"data_list", "experiment_name"}
    assert get_type_hints(CriticalValueExecutionStepContext) == {
        "data_list": list[GenerationData],
        "experiment_name": str,
    }


# Checks that positional and keyword construction produce equal containers.
def test_positional_and_keyword_construction_are_equivalent() -> None:
    data_list = [make_generation_data(7)]

    positional = CriticalValueExecutionStepContext(data_list, "cv_experiment")
    keyword = make_context(data_list=data_list)

    assert positional == keyword


# Checks that two containers sharing the same values are equal.
def test_equality_for_same_values() -> None:
    data_list = [make_generation_data(10)]

    assert make_context(data_list=data_list, experiment_name="same") == make_context(
        data_list=data_list,
        experiment_name="same",
    )


# Checks that a different experiment name makes containers unequal.
@pytest.mark.parametrize("other_name", ["", "OTHER", "cv_experiment "])
def test_inequality_for_different_experiment_name(other_name: str) -> None:
    assert make_context(experiment_name="cv_experiment") != make_context(experiment_name=other_name)


# Checks that a different data list makes containers unequal.
def test_inequality_for_different_data_list() -> None:
    assert make_context(data_list=[make_generation_data(1)]) != make_context(data_list=[make_generation_data(2)])


# Checks that an empty data list is accepted without validation.
def test_accepts_empty_data_list() -> None:
    context = make_context(data_list=[])

    assert context.data_list == []


# Checks that the order of the provided generation data entries is preserved.
def test_preserves_data_list_order() -> None:
    data_list = [make_generation_data(size) for size in (30, 10, 20)]

    assert make_context(data_list=data_list).data_list == data_list


# Checks that omitting a required field raises a TypeError.
@pytest.mark.parametrize("missing_field", ["data_list", "experiment_name"])
def test_omitting_required_field_raises_type_error(missing_field: str) -> None:
    values: dict[str, object] = {"data_list": [], "experiment_name": "cv_experiment"}
    values.pop(missing_field)

    with pytest.raises(TypeError):
        CriticalValueExecutionStepContext(**values)  # type: ignore[arg-type]


# Checks that omitting the data list entirely raises a TypeError.
def test_data_list_has_no_default() -> None:
    with pytest.raises(TypeError):
        CriticalValueExecutionStepContext(experiment_name="cv_experiment")  # type: ignore[call-arg]


# Checks that fields can be reassigned after construction.
def test_fields_are_mutable_after_creation() -> None:
    context = make_context()
    replacement = [make_generation_data(99)]

    context.data_list = replacement
    context.experiment_name = "renamed"

    assert context.data_list is replacement
    assert context.experiment_name == "renamed"


# Checks that the mutable container is not hashable by default.
def test_context_is_not_hashable() -> None:
    with pytest.raises(TypeError):
        hash(make_context())


# Checks that the representation contains the class name and field values.
def test_repr_contains_class_name_and_values() -> None:
    representation = repr(make_context(experiment_name="cv_experiment"))

    assert representation.startswith("CriticalValueExecutionStepContext(")
    assert "cv_experiment" in representation
    assert "GenerationData" in representation


# Checks that asdict converts the container into a plain field mapping.
def test_asdict_returns_plain_field_mapping() -> None:
    context = make_context(data_list=[], experiment_name="cv_experiment")

    assert asdict(context) == {"data_list": [], "experiment_name": "cv_experiment"}
