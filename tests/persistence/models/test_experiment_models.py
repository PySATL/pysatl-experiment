"""Tests for the experiment storage models and interface."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from pysatl_experiment.persistence.models.experiment import ExperimentModel, ExperimentQuery, IExperimentStorage


def make_model(**overrides: Any) -> ExperimentModel:
    """Build an experiment model with deterministic defaults."""
    values: dict[str, Any] = {
        "experiment_type": "power",
        "storage_connection": "sqlite://",
        "run_mode": "reuse",
        "report_mode": "without-chart",
        "hypothesis": "normal",
        "generator_type": "standard",
        "executor_type": "standard",
        "report_builder_type": "standard",
        "sample_sizes": [10, 20],
        "monte_carlo_count": 100,
        "criteria": {"KS": [0.05]},
        "alternatives": {"NORM": [0.0, 1.0]},
        "significance_levels": [0.05],
        "parallel_workers": 1,
        "is_generation_done": False,
        "is_execution_done": False,
        "is_report_building_done": False,
    }
    values.update(overrides)
    return ExperimentModel(**values)


def make_query(**overrides: Any) -> ExperimentQuery:
    """Build an experiment query with deterministic defaults."""
    values: dict[str, Any] = {
        "experiment_type": "power",
        "storage_connection": "sqlite://",
        "run_mode": "reuse",
        "hypothesis": "normal",
        "generator_type": "standard",
        "executor_type": "standard",
        "report_builder_type": "standard",
        "sample_sizes": [10, 20],
        "monte_carlo_count": 100,
        "criteria": {"KS": [0.05]},
        "alternatives": {"NORM": [0.0, 1.0]},
        "significance_levels": [0.05],
        "report_mode": "without-chart",
        "parallel_workers": 1,
    }
    values.update(overrides)
    return ExperimentQuery(**values)


# Checks that the experiment model keeps every provided field.
def test_experiment_model_stores_all_fields() -> None:
    model = make_model(is_execution_done=True, is_report_building_done=True)

    assert model.experiment_type == "power"
    assert model.storage_connection == "sqlite://"
    assert model.run_mode == "reuse"
    assert model.report_mode == "without-chart"
    assert model.hypothesis == "normal"
    assert model.generator_type == "standard"
    assert model.executor_type == "standard"
    assert model.report_builder_type == "standard"
    assert model.sample_sizes == [10, 20]
    assert model.monte_carlo_count == 100
    assert model.criteria == {"KS": [0.05]}
    assert model.alternatives == {"NORM": [0.0, 1.0]}
    assert model.significance_levels == [0.05]
    assert model.parallel_workers == 1
    assert model.is_generation_done is False
    assert model.is_execution_done is True
    assert model.is_report_building_done is True


# Checks that the experiment model rejects unknown constructor arguments.
def test_experiment_model_rejects_unknown_field() -> None:
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        ExperimentModel(experiment_type="power", unknown_field="x")  # type: ignore[call-arg]


# Checks that the experiment query keeps every provided field.
def test_experiment_query_stores_all_fields() -> None:
    query = make_query()

    assert query.experiment_type == "power"
    assert query.storage_connection == "sqlite://"
    assert query.run_mode == "reuse"
    assert query.hypothesis == "normal"
    assert query.generator_type == "standard"
    assert query.executor_type == "standard"
    assert query.report_builder_type == "standard"
    assert query.sample_sizes == [10, 20]
    assert query.monte_carlo_count == 100
    assert query.criteria == {"KS": [0.05]}
    assert query.alternatives == {"NORM": [0.0, 1.0]}
    assert query.significance_levels == [0.05]
    assert query.report_mode == "without-chart"
    assert query.parallel_workers == 1


# Checks that two queries with identical values compare equal.
def test_experiment_query_equality() -> None:
    assert make_query() == make_query()
    assert make_query() != make_query(hypothesis="exponential")


# Checks that the experiment storage interface declares its four own abstract methods.
def test_experiment_storage_declares_expected_abstract_methods() -> None:
    assert {"get_experiment_id", "set_generation_done", "set_execution_done", "set_report_building_done"} <= set(
        IExperimentStorage.__abstractmethods__
    )


# Checks that the abstract lookup body is reachable through the base class.
def test_experiment_storage_get_experiment_id_body_returns_none() -> None:
    assert IExperimentStorage.get_experiment_id(MagicMock(), make_query()) is None


# Checks that the abstract progress-marker bodies are reachable through the base class.
@pytest.mark.parametrize(
    "method_name",
    [
        pytest.param("set_generation_done", id="generation"),
        pytest.param("set_execution_done", id="execution"),
        pytest.param("set_report_building_done", id="report-building"),
    ],
)
def test_experiment_storage_progress_marker_bodies_return_none(method_name: str) -> None:
    assert getattr(IExperimentStorage, method_name)(MagicMock(), 7) is None
