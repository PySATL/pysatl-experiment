"""Tests for the alternative hypothesis validation schema."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from pysatl_criterion.generator.generators import CauchyRVSGenerator, NormalGenerator

from pysatl_experiment.cli.validation.schemas.alternative import (
    Alternative,
    AlternativesConfig,
    _base_generator_params,
    _get_available_generator_classes,
)
from pysatl_experiment.configuration.models.experiment_type import ExperimentType


class NakiGenerator(NormalGenerator):
    """Generator stub whose name shares the ``N`` prefix with ``NormalGenerator``."""


@pytest.fixture()
def stub_generators() -> Any:
    """Expose a stable generator registry for the validation tests."""
    with patch(
        "pysatl_experiment.cli.validation.schemas.alternative._get_available_generator_classes",
        return_value=[NormalGenerator, CauchyRVSGenerator],
    ):
        yield


@pytest.fixture()
def ambiguous_generators() -> Any:
    """Expose a registry whose two generator names share a common prefix."""
    with patch(
        "pysatl_experiment.cli.validation.schemas.alternative._get_available_generator_classes",
        return_value=[NormalGenerator, NakiGenerator],
    ):
        yield


# Checks that the registry lookup returns the generators sorted by class name.
def test_get_available_generator_classes_is_sorted() -> None:
    classes = _get_available_generator_classes()

    assert classes == sorted(classes, key=lambda cls: cls.__name__)


# Checks that the cached base parameter names exclude the concrete parameters.
def test_base_generator_params_are_cached() -> None:
    first = _base_generator_params()
    second = _base_generator_params()

    assert first is second
    assert "self" in first


# Checks that an unmatched generator prefix is reported with the available names.
def test_unknown_generator_prefix_is_rejected(stub_generators: Any) -> None:
    with pytest.raises(ValidationError, match="did not match any available generators"):
        Alternative(generator_name="NoSuchGenerator", parameters=[])


# Checks that an ambiguous generator prefix is reported with the matching names.
def test_ambiguous_generator_prefix_is_rejected(ambiguous_generators: Any) -> None:
    with pytest.raises(ValidationError, match="is ambiguous") as exc_info:
        Alternative(generator_name="N", parameters=[1.0, 0.5])

    message = str(exc_info.value)
    assert "NAKIGENERATOR" in message
    assert "NORMALGENERATOR" in message
    assert "Please be more specific" in message


# Checks that a space separated string is parsed into name and parameters.
@pytest.mark.parametrize(
    ("raw", "expected_name", "expected_parameters"),
    [
        pytest.param("NormalG 1.0 0.5", "NORMALGENERATOR", [1.0, 0.5], id="normal-generator"),
        pytest.param("cauchy 0 2", "CAUCHYRVSGENERATOR", [0.0, 2.0], id="cauchy-generator"),
    ],
)
def test_alternative_is_parsed_from_string(
    stub_generators: Any, raw: str, expected_name: str, expected_parameters: list[float]
) -> None:
    alternative = Alternative.model_validate(raw)

    assert alternative.generator_name == expected_name
    assert alternative.parameters == expected_parameters


# Checks that a whitespace-only string is rejected as empty.
def test_empty_alternative_string_is_rejected(stub_generators: Any) -> None:
    with pytest.raises(ValidationError, match="Alternative string cannot be empty."):
        Alternative.model_validate("   ")


# Checks that non-numeric parameters are rejected with the generator name.
def test_non_numeric_parameters_are_rejected(stub_generators: Any) -> None:
    with pytest.raises(ValidationError, match="must be numbers"):
        Alternative.model_validate("NormalG abc def")


# Checks that a dictionary input bypasses the string parsing validator.
def test_dictionary_input_skips_string_parsing(stub_generators: Any) -> None:
    alternative = Alternative.model_validate({"generator_name": "NormalG", "parameters": [1.0, 0.5]})

    assert alternative.generator_name == "NORMALGENERATOR"
    assert alternative.parameters == [1.0, 0.5]


# Checks that a parameter count mismatch is reported with the expected count.
def test_parameter_count_mismatch_is_rejected(stub_generators: Any) -> None:
    with pytest.raises(ValidationError, match="but received 3"):
        Alternative(generator_name="NormalG", parameters=[1.0, 0.5, 2.0])


# Checks that no parameters at all is rejected when the generator expects some.
def test_missing_parameters_are_rejected(stub_generators: Any) -> None:
    with pytest.raises(ValidationError, match="but received 0"):
        Alternative(generator_name="NormalG", parameters=[])


# Checks that alternatives default to an empty list for power experiments.
def test_alternatives_config_defaults_to_empty_list() -> None:
    config = AlternativesConfig(experiment_type=ExperimentType.POWER)

    assert config.alternatives == []


# Checks that alternatives are accepted for a power experiment.
def test_alternatives_config_accepts_power_alternatives(stub_generators: Any) -> None:
    config = AlternativesConfig(experiment_type=ExperimentType.POWER, alternatives=["NormalG 1.0 0.5"])  # type: ignore[list-item]

    assert len(config.alternatives) == 1
    assert config.alternatives[0].generator_name == "NORMALGENERATOR"


# Checks that a non-power experiment type without alternatives stays valid.
def test_alternatives_config_allows_empty_list_for_other_types() -> None:
    config = AlternativesConfig(experiment_type=ExperimentType.CRITICAL_VALUE)

    assert config.alternatives == []
    assert config.experiment_type == ExperimentType.CRITICAL_VALUE


# Checks that alternatives are rejected for a non-power experiment type.
@pytest.mark.parametrize(
    "experiment_type",
    [
        pytest.param(ExperimentType.CRITICAL_VALUE, id="critical-value"),
        pytest.param(ExperimentType.TIME_COMPLEXITY, id="time-complexity"),
    ],
)
def test_alternatives_config_rejects_non_power_experiment_type(
    stub_generators: Any, experiment_type: ExperimentType
) -> None:
    with pytest.raises(ValidationError, match="Alternatives are not supported for the experiment type") as exc_info:
        AlternativesConfig(experiment_type=experiment_type, alternatives=["NormalG 1.0 0.5"])  # type: ignore[list-item]

    assert experiment_type.value in str(exc_info.value)


# Checks that the non-power rejection only triggers when alternatives are present.
@pytest.mark.parametrize(
    "experiment_type",
    [
        pytest.param(ExperimentType.CRITICAL_VALUE, id="critical-value"),
        pytest.param(ExperimentType.TIME_COMPLEXITY, id="time-complexity"),
    ],
)
def test_alternatives_config_allows_non_power_experiment_type_without_alternatives(
    experiment_type: ExperimentType,
) -> None:
    config = AlternativesConfig(experiment_type=experiment_type, alternatives=[])

    assert config.alternatives == []
    assert config.experiment_type == experiment_type

    assert config.alternatives == []
