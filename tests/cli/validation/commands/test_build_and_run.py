"""Tests for the build-and-run configuration validation command."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click import ClickException
from pysatl_criterion import DistributionType

from pysatl_experiment.cli.validation.commands import build_and_run as br_module
from pysatl_experiment.cli.validation.commands.build_and_run import (
    _adapt_pydantic_to_dataclass,
    _check_if_experiment_finished,
    _get_experiment_config_from_storage,
    _save_experiment_config_to_storage,
    validate_build_and_run,
)
from pysatl_experiment.cli.validation.schemas.experiment import BaseExperimentConfig as PydanticBaseExperiment
from pysatl_experiment.cli.validation.schemas.experiment import ExperimentConfig as ExperimentInputSchema
from pysatl_experiment.cli.validation.schemas.experiment import TimeComplexityConfig as PydanticTimeComplexityConfig
from pysatl_experiment.configuration.experiment_config.critical_value_experiment_config import (
    CriticalValueExperimentConfig,
)
from pysatl_experiment.configuration.experiment_config.power_experiment_config import PowerExperimentConfig
from pysatl_experiment.configuration.experiment_config.time_complexity_experiment_config import (
    TimeComplexityExperimentConfig,
)
from pysatl_experiment.configuration.experiment_data.experiment_data import ExperimentData
from pysatl_experiment.configuration.models.alternative import Alternative
from pysatl_experiment.configuration.models.criterion import Criterion
from pysatl_experiment.configuration.models.experiment_type import ExperimentType
from pysatl_experiment.configuration.models.report_mode import ReportMode
from pysatl_experiment.configuration.models.run_mode import RunMode
from pysatl_experiment.configuration.models.step_type import StepType
from pysatl_experiment.configuration.models.steps_done import StepsDone
from pysatl_experiment.persistence.models.experiment import ExperimentModel


def _raw_config(experiment_type: str = "time_complexity", **overrides: Any) -> dict:
    """Build a raw experiment configuration dictionary as read from a config file."""
    config: dict[str, Any] = {
        "experiment_type": experiment_type,
        "hypothesis": "normal",
        "run_mode": "reuse",
        "report_mode": "with-chart",
        "generator_type": "standard",
        "executor_type": "standard",
        "report_builder_type": "standard",
        "criteria": [{"criterion_code": "KS", "parameters": []}],
        "storage_connection": "sqlite://",
        "sample_sizes": [10],
        "monte_carlo_count": 100,
        "parallel_workers": 1,
    }
    config.update(overrides)
    return {"name": "exp", "config": config}


def _legacy_base() -> dict[str, Any]:
    """Return the shared legacy dataclass fields used by every config variant."""
    return {
        "storage_connection": "sqlite://",
        "run_mode": RunMode.REUSE,
        "hypothesis": DistributionType.NORMAL,
        "hypothesis_params": {},
        "generator_type": StepType.STANDARD,
        "executor_type": StepType.STANDARD,
        "report_builder_type": StepType.STANDARD,
        "sample_sizes": [10],
        "monte_carlo_count": 100,
        "criteria": [Criterion(criterion_code="KS", parameters=[])],
        "report_mode": ReportMode.WITH_CHART,
        "parallel_workers": 1,
    }


def _legacy_time_complexity_config() -> TimeComplexityExperimentConfig:
    return TimeComplexityExperimentConfig(experiment_type=ExperimentType.TIME_COMPLEXITY, **_legacy_base())


def _legacy_critical_value_config() -> CriticalValueExperimentConfig:
    return CriticalValueExperimentConfig(
        experiment_type=ExperimentType.CRITICAL_VALUE, significance_levels=[0.05], **_legacy_base()
    )


def _legacy_power_config() -> PowerExperimentConfig:
    return PowerExperimentConfig(
        experiment_type=ExperimentType.POWER,
        significance_levels=[0.05],
        alternatives=[Alternative(parameters=[1.0], distribution_type=DistributionType.NORMAL)],
        **_legacy_base(),
    )


def _experiment_model(**overrides: Any) -> ExperimentModel:
    """Build a stored experiment model with all flags defaulting to incomplete."""
    model: dict[str, Any] = {
        "experiment_type": "time_complexity",
        "storage_connection": "sqlite://",
        "run_mode": "reuse",
        "report_mode": "with-chart",
        "hypothesis": "normal",
        "generator_type": "standard",
        "executor_type": "standard",
        "report_builder_type": "standard",
        "sample_sizes": [10],
        "monte_carlo_count": 100,
        "criteria": {"KS": []},
        "alternatives": {},
        "significance_levels": [],
        "parallel_workers": 1,
        "is_generation_done": False,
        "is_execution_done": False,
        "is_report_building_done": False,
    }
    model.update(overrides)
    return ExperimentModel(**model)


# Checks a brand new experiment is validated, persisted and returned as ExperimentData.
@patch.object(br_module, "ensure_result_dir", return_value=Path("results"))
@patch.object(br_module, "AlchemyExperimentStorage")
@patch.object(br_module, "_adapt_pydantic_to_dataclass")
def test_validate_build_and_run_creates_new_experiment(
    adapt: MagicMock, storage_cls: MagicMock, ensure_result_dir: MagicMock
) -> None:
    legacy_config = _legacy_time_complexity_config()
    adapt.return_value = legacy_config
    storage = storage_cls.return_value
    storage.get_data.return_value = None

    result = validate_build_and_run(_raw_config())

    assert isinstance(result, ExperimentData)
    assert result.experiment_name == "exp"
    assert result.config is legacy_config
    assert result.steps_done == StepsDone(False, False, False)
    assert result.results_path == Path("results")
    storage.init.assert_called_once()
    storage.insert_data.assert_called_once()
    ensure_result_dir.assert_called_once_with()


# Checks that a partially executed experiment is resumed with its stored step state.
@patch.object(br_module, "ensure_result_dir", return_value=Path("results"))
@patch.object(br_module, "AlchemyExperimentStorage")
@patch.object(br_module, "_adapt_pydantic_to_dataclass")
def test_validate_build_and_run_resumes_existing_experiment(
    adapt: MagicMock, storage_cls: MagicMock, ensure_result_dir: MagicMock
) -> None:
    adapt.return_value = _legacy_time_complexity_config()
    storage_cls.return_value.get_data.return_value = _experiment_model(is_generation_done=True)

    result = validate_build_and_run(_raw_config())

    assert result.steps_done == StepsDone(True, False, False)
    storage_cls.return_value.insert_data.assert_not_called()


# Checks that a fully finished experiment raises a ClickException instead of rerunning.
@patch.object(br_module, "ensure_result_dir")
@patch.object(br_module, "AlchemyExperimentStorage")
@patch.object(br_module, "_adapt_pydantic_to_dataclass")
def test_validate_build_and_run_rejects_finished_experiment(
    adapt: MagicMock, storage_cls: MagicMock, ensure_result_dir: MagicMock
) -> None:
    adapt.return_value = _legacy_time_complexity_config()
    storage_cls.return_value.get_data.return_value = _experiment_model(
        is_generation_done=True, is_execution_done=True, is_report_building_done=True
    )

    with pytest.raises(ClickException, match="already finished"):
        validate_build_and_run(_raw_config())


# Checks a power experiment builds a SQLiteCriticalValueChecker from its storage connection.
@patch.object(br_module, "SQLiteCriticalValueChecker")
def test_validate_build_and_run_creates_checker_for_power(checker_cls: MagicMock) -> None:
    with pytest.raises(ClickException):
        validate_build_and_run(_raw_config(experiment_type="power", storage_connection="sqlite:///pysatl.sqlite"))

    checker_cls.assert_called_once_with(connection_string="sqlite:///pysatl.sqlite")


# Checks a power experiment without a storage connection reports a helpful error.
@patch.object(br_module, "SQLiteCriticalValueChecker")
def test_validate_build_and_run_power_without_connection_raises(checker_cls: MagicMock) -> None:
    raw = _raw_config(experiment_type="power")
    raw["config"].pop("storage_connection")

    with pytest.raises(ClickException, match="storage_connection"):
        validate_build_and_run(raw)

    checker_cls.assert_not_called()


# Checks that missing, value-error and other pydantic errors are all surfaced in one message.
def test_validate_build_and_run_reports_all_validation_errors() -> None:
    raw = _raw_config(run_mode="not-a-mode", sample_sizes=[5])
    raw["config"].pop("storage_connection")

    with pytest.raises(ClickException) as exc_info:
        validate_build_and_run(raw)

    message = str(exc_info.value)
    assert "A required parameter is missing: 'config.time_complexity.storage_connection'" in message
    assert "Sample sizes must be greater than 10." in message
    assert "Error in the field 'config.time_complexity.run_mode'" in message


# Checks that an unmapped pydantic configuration type raises TypeError.
def test_adapt_pydantic_to_dataclass_raises_for_unmapped_type() -> None:
    config = PydanticBaseExperiment(
        hypothesis=DistributionType.NORMAL,
        run_mode=RunMode.REUSE,
        report_mode=ReportMode.WITH_CHART,
        generator_type=StepType.STANDARD,
        executor_type=StepType.STANDARD,
        report_builder_type=StepType.STANDARD,
        criteria=[],
        storage_connection="sqlite://",
        sample_sizes=[10],
        monte_carlo_count=100,
        parallel_workers=1,
    )

    with pytest.raises(TypeError, match="No match for Pydantic type"):
        _adapt_pydantic_to_dataclass(config)


# Checks that a supported pydantic configuration is translated through dacite.
@patch.object(br_module, "from_dict")
def test_adapt_pydantic_to_dataclass_maps_supported_config(from_dict_mock: MagicMock) -> None:
    validated = ExperimentInputSchema.model_validate(_raw_config())
    from_dict_mock.return_value = _legacy_time_complexity_config()

    # The adapter only handles the legacy pipeline, so narrow the discriminated union the
    # same way build_and_run narrows it before calling.
    config = validated.config
    assert isinstance(config, PydanticTimeComplexityConfig)

    result = _adapt_pydantic_to_dataclass(config)

    assert result is from_dict_mock.return_value
    from_dict_mock.assert_called_once()
    kwargs = from_dict_mock.call_args.kwargs
    assert kwargs["data_class"] is TimeComplexityExperimentConfig
    assert kwargs["data"]["experiment_type"] == "time_complexity"


# Checks that the storage lookup builds a matching query for each experiment type.
@pytest.mark.parametrize(
    ("config_factory", "expected_type"),
    [
        (_legacy_time_complexity_config, "time_complexity"),
        (_legacy_critical_value_config, "critical_value"),
        (_legacy_power_config, "power"),
    ],
)
def test_get_experiment_config_from_storage_uses_config(config_factory, expected_type: str) -> None:
    storage = MagicMock()
    storage.get_data.return_value = "sentinel"

    result = _get_experiment_config_from_storage(config_factory(), storage)

    assert result == "sentinel"
    query = storage.get_data.call_args.args[0]
    assert query.experiment_type == expected_type
    assert query.storage_connection == "sqlite://"


# Checks that power alternatives are flattened into a distribution-to-parameters mapping.
def test_get_experiment_config_from_storage_maps_power_alternatives() -> None:
    storage = MagicMock()
    storage.get_data.return_value = None

    _get_experiment_config_from_storage(_legacy_power_config(), storage)

    query = storage.get_data.call_args.args[0]
    assert query.alternatives == {"normal": [1.0]}
    assert query.significance_levels == [0.05]


# Checks that saving a new experiment persists an ExperimentModel with the expected fields.
@pytest.mark.parametrize(
    ("config_factory", "expected_type"),
    [
        (_legacy_time_complexity_config, "time_complexity"),
        (_legacy_critical_value_config, "critical_value"),
        (_legacy_power_config, "power"),
    ],
)
def test_save_experiment_config_to_storage_inserts_model(config_factory, expected_type: str) -> None:
    storage = MagicMock()

    _save_experiment_config_to_storage(config_factory(), storage)

    storage.insert_data.assert_called_once()
    model = storage.insert_data.call_args.args[0]
    assert isinstance(model, ExperimentModel)
    assert model.experiment_type == expected_type
    assert model.criteria == {"KS": []}
    assert model.storage_connection == "sqlite://"
    assert model.is_generation_done is False
    assert model.is_execution_done is False
    assert model.is_report_building_done is False


# Checks that power alternatives are converted when persisting a new experiment.
def test_save_experiment_config_to_storage_maps_power_alternatives() -> None:
    storage = MagicMock()

    _save_experiment_config_to_storage(_legacy_power_config(), storage)

    model = storage.insert_data.call_args.args[0]
    assert model.alternatives == {"normal": [1.0]}
    assert model.significance_levels == [0.05]


# Checks that a fully completed experiment raises a ClickException.
def test_check_if_experiment_finished_raises_when_done() -> None:
    model = _experiment_model(is_generation_done=True, is_execution_done=True, is_report_building_done=True)

    with pytest.raises(ClickException, match="already finished"):
        _check_if_experiment_finished(model)


# Checks that partial completion is reported through a StepsDone snapshot.
@pytest.mark.parametrize(
    ("is_generation_done", "is_execution_done", "is_report_building_done"),
    [(True, False, False), (True, True, False), (False, True, True)],
)
def test_check_if_experiment_finished_returns_steps(
    is_generation_done: bool, is_execution_done: bool, is_report_building_done: bool
) -> None:
    model = _experiment_model(
        is_generation_done=is_generation_done,
        is_execution_done=is_execution_done,
        is_report_building_done=is_report_building_done,
    )

    result = _check_if_experiment_finished(model)

    assert result == StepsDone(is_generation_done, is_execution_done, is_report_building_done)
