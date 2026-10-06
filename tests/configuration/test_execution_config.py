"""Tests for experiment execution configuration model."""

from dataclasses import asdict, fields, is_dataclass, replace
from typing import get_type_hints

import pytest

from pysatl_experiment.configuration.execution_config import ExecutionConfig
from pysatl_experiment.configuration.models.step_type import StepType


class TestExecutionConfig:
    # Checks that a config stores the provided executor type and worker count as-is.
    def test_creation_with_valid_fields(self) -> None:
        config = ExecutionConfig(executor_type=StepType.STANDARD, parallel_workers=4)

        assert config.executor_type is StepType.STANDARD
        assert config.parallel_workers == 4

    # Checks that the model accepts every available StepType value.
    @pytest.mark.parametrize("step_type", list(StepType))
    def test_creation_with_every_step_type(self, step_type: StepType) -> None:
        config = ExecutionConfig(executor_type=step_type, parallel_workers=1)

        assert config.executor_type is step_type

    # Checks that positional and keyword construction produce equal configs.
    def test_positional_and_keyword_construction_are_equivalent(self) -> None:
        positional = ExecutionConfig(StepType.CUSTOM, 5)
        keyword = ExecutionConfig(executor_type=StepType.CUSTOM, parallel_workers=5)

        assert positional == keyword

    # Checks that both fields are required and omitting one raises a TypeError.
    def test_omitting_required_field_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            ExecutionConfig(executor_type=StepType.STANDARD)  # type: ignore[call-arg]

    # Checks that the model declares exactly the two documented dataclass fields with their types.
    def test_declares_expected_dataclass_fields(self) -> None:
        assert is_dataclass(ExecutionConfig)

        assert [field.name for field in fields(ExecutionConfig)] == ["executor_type", "parallel_workers"]
        assert get_type_hints(ExecutionConfig) == {"executor_type": StepType, "parallel_workers": int}

    # Checks that two configs with identical field values compare equal.
    def test_equality_for_identical_values(self) -> None:
        assert ExecutionConfig(StepType.STANDARD, 2) == ExecutionConfig(StepType.STANDARD, 2)

    # Checks that configs differing in any single field compare unequal.
    @pytest.mark.parametrize(
        ("left", "right"),
        [
            (ExecutionConfig(StepType.STANDARD, 2), ExecutionConfig(StepType.CUSTOM, 2)),
            (ExecutionConfig(StepType.STANDARD, 2), ExecutionConfig(StepType.STANDARD, 3)),
        ],
    )
    def test_inequality_for_any_different_field(self, left: ExecutionConfig, right: ExecutionConfig) -> None:
        assert left != right

    # Checks that the generated repr contains the class name and both field values.
    def test_repr_contains_field_values(self) -> None:
        representation = repr(ExecutionConfig(StepType.CUSTOM, 8))

        assert representation.startswith("ExecutionConfig(")
        assert "custom" in representation
        assert "8" in representation

    # Checks that asdict converts the config into a plain field-to-value mapping.
    def test_asdict_returns_plain_field_mapping(self) -> None:
        config = ExecutionConfig(StepType.STANDARD, 3)

        assert asdict(config) == {"executor_type": StepType.STANDARD, "parallel_workers": 3}

    # Checks that replace returns an updated copy and leaves the original config untouched.
    def test_replace_returns_updated_copy(self) -> None:
        config = ExecutionConfig(StepType.STANDARD, 2)

        updated = replace(config, parallel_workers=6)

        assert updated == ExecutionConfig(StepType.STANDARD, 6)
        assert config.parallel_workers == 2

    # Checks that config fields can be reassigned after construction.
    def test_fields_are_mutable_after_creation(self) -> None:
        config = ExecutionConfig(StepType.STANDARD, 1)

        config.executor_type = StepType.CUSTOM
        config.parallel_workers = 7

        assert config == ExecutionConfig(StepType.CUSTOM, 7)

    # Checks that mutable configs are not hashable by default.
    def test_config_is_not_hashable(self) -> None:
        with pytest.raises(TypeError):
            hash(ExecutionConfig(StepType.STANDARD, 1))

    # Checks that unusual worker counts are stored without any validation logic.
    @pytest.mark.parametrize("parallel_workers", [0, -1, 10**6])
    def test_parallel_workers_are_not_validated(self, parallel_workers: int) -> None:
        config = ExecutionConfig(executor_type=StepType.STANDARD, parallel_workers=parallel_workers)

        assert config.parallel_workers == parallel_workers

    # Checks that the executor type field accepts arbitrary values without runtime type checking.
    def test_executor_type_accepts_arbitrary_value(self) -> None:
        config = ExecutionConfig(executor_type="standard", parallel_workers=1)  # type: ignore[arg-type]

        assert config.executor_type == "standard"
