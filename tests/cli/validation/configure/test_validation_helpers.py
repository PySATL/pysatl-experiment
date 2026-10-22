"""Tests for the optional-argument guards and worker limits of the configure command."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click import BadParameter, ClickException
from pydantic import ValidationError
from pysatl_criterion.generator.generators import NormalGenerator

from pysatl_experiment.cli.commands.configure import (
    _configure_alternatives,
    _configure_experiment_type,
    _configure_hypothesis,
    _configure_hypothesis_params,
    _configure_monte_carlo_count,
    _configure_sample_sizes,
    _configure_significance_levels,
    _configure_storage_connection,
    _configure_workers,
)


# Checks that each optional helper leaves the config untouched when given None.
@pytest.mark.parametrize(
    ("helper", "config_key"),
    [
        pytest.param(_configure_sample_sizes, "sample_sizes", id="sample-sizes"),
        pytest.param(_configure_experiment_type, "experiment_type", id="experiment-type"),
        pytest.param(_configure_monte_carlo_count, "monte_carlo_count", id="monte-carlo-count"),
        pytest.param(_configure_hypothesis, "hypothesis", id="hypothesis"),
        pytest.param(_configure_hypothesis_params, "hypothesis_params", id="hypothesis-params"),
        pytest.param(_configure_significance_levels, "significance_levels", id="significance-levels"),
        pytest.param(_configure_alternatives, "alternatives", id="alternatives"),
        pytest.param(_configure_workers, "parallel_workers", id="workers"),
    ],
)
def test_optional_helpers_ignore_none(helper: Any, config_key: str) -> None:
    experiment_config: dict[str, Any] = {"existing": 1}

    helper(experiment_config, None)

    assert experiment_config == {"existing": 1}
    assert config_key not in experiment_config


# Checks that the sample sizes helper converts the tuple into a list.
def test_sample_sizes_are_stored_as_list() -> None:
    experiment_config: dict[str, Any] = {}

    _configure_sample_sizes(experiment_config, (10, 20, 30))

    assert experiment_config["sample_sizes"] == [10, 20, 30]


# Checks that the experiment type helper stores the normalized value.
def test_experiment_type_is_normalized() -> None:
    experiment_config: dict[str, Any] = {}

    _configure_experiment_type(experiment_config, "POWER")

    assert experiment_config["experiment_type"] == "power"


# Checks that the Monte-Carlo count helper stores the value as-is.
def test_monte_carlo_count_is_stored() -> None:
    experiment_config: dict[str, Any] = {}

    _configure_monte_carlo_count(experiment_config, 154)

    assert experiment_config["monte_carlo_count"] == 154


# Checks that the hypothesis helper also refreshes the criteria list.
@patch("pysatl_experiment.cli.commands.configure.criteria_from_codes")
@patch("pysatl_experiment.cli.commands.configure.get_statistics_short_codes_for_hypothesis")
def test_hypothesis_helper_refreshes_criteria(get_codes: MagicMock, criteria_from_codes: MagicMock) -> None:
    get_codes.return_value = ["KS", "AD"]
    criteria_from_codes.return_value = [{"criterion_code": "KS"}]
    experiment_config: dict[str, Any] = {}

    _configure_hypothesis(experiment_config, "NORMAL")

    assert experiment_config["hypothesis"] == "normal"
    assert experiment_config["criteria"] == [{"criterion_code": "KS"}]
    get_codes.assert_called_once_with("normal")
    criteria_from_codes.assert_called_once_with(["KS", "AD"])


# Checks that the significance levels helper converts the tuple into a list.
def test_significance_levels_are_stored_as_list() -> None:
    experiment_config: dict[str, Any] = {}

    _configure_significance_levels(experiment_config, (0.05, 0.01))

    assert experiment_config["significance_levels"] == [0.05, 0.01]


# Checks that significance levels are rejected for time complexity experiments.
def test_significance_levels_rejected_for_time_complexity() -> None:
    experiment_config: dict[str, Any] = {"experiment_type": "time_complexity"}

    with pytest.raises(ClickException, match="not supported for time complexity"):
        _configure_significance_levels(experiment_config, (0.05,))

    assert "significance_levels" not in experiment_config


# Checks that the storage connection is stored without validation.
def test_storage_connection_is_stored() -> None:
    experiment_config: dict[str, Any] = {}

    _configure_storage_connection(experiment_config, "postgresql://localhost/pysatl")

    assert experiment_config["storage_connection"] == "postgresql://localhost/pysatl"


# Checks that a worker count within the CPU limit is accepted.
@patch("pysatl_experiment.cli.commands.configure.mp.cpu_count", return_value=8)
def test_workers_within_cpu_limit_are_accepted(cpu_count: MagicMock) -> None:
    experiment_config: dict[str, Any] = {}

    _configure_workers(experiment_config, 4)

    assert experiment_config["parallel_workers"] == 4
    cpu_count.assert_called_once_with()


# Checks that a worker count above the CPU limit is rejected with guidance.
@patch("pysatl_experiment.cli.commands.configure.mp.cpu_count", return_value=8)
def test_workers_above_cpu_limit_are_rejected(cpu_count: MagicMock) -> None:
    experiment_config: dict[str, Any] = {}

    with pytest.raises(ClickException) as exc_info:
        _configure_workers(experiment_config, 64)

    message = str(exc_info.value)
    assert "Cannot set parallel workers to 64" in message
    assert "only 8 CPU cores" in message
    assert "between 1 and 8" in message
    assert "parallel_workers" not in experiment_config


def _validation_error(loc: tuple[Any, ...], message: str) -> ValidationError:
    """Build a single-error pydantic ValidationError with the given location."""
    return ValidationError.from_exception_data(
        "AlternativesConfig",
        [{"type": "value_error", "loc": loc, "input": "NoSuch 1.0", "ctx": {"error": ValueError(message)}}],
    )


# Checks that a per-alternative validation error names the offending input.
@patch("pysatl_experiment.cli.commands.configure.AlternativesConfig")
def test_alternatives_error_names_offending_input(alternatives_config: MagicMock) -> None:
    alternatives_config.side_effect = _validation_error(
        ("alternatives", 0), "Generator prefix 'NoSuch' did not match any available generators."
    )
    experiment_config: dict[str, Any] = {"experiment_type": "power"}

    with pytest.raises(ClickException) as exc_info:
        _configure_alternatives(experiment_config, ("NoSuch 1.0",))

    message = str(exc_info.value)
    assert "For alternative #1 ('NoSuch 1.0')" in message
    assert "did not match any available generators" in message
    assert "alternatives" not in experiment_config


# Checks that a whole-field alternatives error is rendered with a bullet.
@patch("pysatl_experiment.cli.commands.configure.AlternativesConfig")
def test_alternatives_field_error_is_rendered_with_bullet(alternatives_config: MagicMock) -> None:
    alternatives_config.side_effect = _validation_error(("alternatives",), "Alternatives are malformed.")
    experiment_config: dict[str, Any] = {"experiment_type": "power"}

    with pytest.raises(ClickException) as exc_info:
        _configure_alternatives(experiment_config, ("NoSuch 1.0",))

    assert "- Alternatives are malformed." in str(exc_info.value).replace("Value error, ", "")
    assert "In field 'experiment_type'" not in str(exc_info.value)


# Checks that an error outside the alternatives field names that field instead.
@patch("pysatl_experiment.cli.commands.configure.AlternativesConfig")
def test_non_alternatives_error_names_the_field(alternatives_config: MagicMock) -> None:
    alternatives_config.side_effect = _validation_error(("experiment_type",), "Unsupported experiment type.")
    experiment_config: dict[str, Any] = {"experiment_type": "power"}

    with pytest.raises(ClickException) as exc_info:
        _configure_alternatives(experiment_config, ("NoSuch 1.0",))

    assert "In field 'experiment_type'" in str(exc_info.value)
    assert "Unsupported experiment type." in str(exc_info.value)


# Checks that a validated alternatives payload is stored on the config.
@patch(
    "pysatl_experiment.cli.validation.schemas.alternative._get_available_generator_classes",
    return_value=[NormalGenerator],
)
def test_alternatives_are_stored_when_valid(stub_registry: MagicMock) -> None:
    experiment_config: dict[str, Any] = {"experiment_type": "power"}

    _configure_alternatives(experiment_config, ("NormalG 1.0 0.5",))

    assert experiment_config["alternatives"] == [{"generator_name": "NORMALGENERATOR", "parameters": [1.0, 0.5]}]


# Checks that a valid JSON object is parsed and stored as hypothesis params.
def test_hypothesis_params_are_stored_as_parsed_object() -> None:
    experiment_config: dict[str, Any] = {}

    _configure_hypothesis_params(experiment_config, '{"beta": 2.0, "scale": 3}')

    assert experiment_config["hypothesis_params"] == {"beta": 2.0, "scale": 3}


# Checks that malformed JSON input is rejected as a bad parameter.
def test_hypothesis_params_rejects_invalid_json() -> None:
    experiment_config: dict[str, Any] = {}

    with pytest.raises(BadParameter, match="must be a JSON object"):
        _configure_hypothesis_params(experiment_config, "{not json")

    assert "hypothesis_params" not in experiment_config


# Checks that valid JSON which is not an object is rejected.
def test_hypothesis_params_rejects_non_object_json() -> None:
    experiment_config: dict[str, Any] = {}

    with pytest.raises(BadParameter, match="must be a JSON object, got: list"):
        _configure_hypothesis_params(experiment_config, "[1.0, 2.0]")

    assert "hypothesis_params" not in experiment_config


# Checks that non-numeric distribution parameter values are rejected.
def test_hypothesis_params_rejects_non_numeric_values() -> None:
    experiment_config: dict[str, Any] = {}

    with pytest.raises(BadParameter, match="must be a number, got str"):
        _configure_hypothesis_params(experiment_config, '{"beta": "2.0"}')

    assert "hypothesis_params" not in experiment_config
